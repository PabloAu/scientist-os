"""Transport behavior uses a mock HTTP transport: no model inference or paid calls."""

import json

import httpx
import pytest

from scientist_os.agent import AgentRunner
from scientist_os.providers import OpenAICompatibleProvider, ProviderError, redact, tool_message
from scientist_os.workspace import Workspace


def mock_transport(monkeypatch, handler):
    original = httpx.Client
    configurations = []

    def client(**kwargs):
        configurations.append(kwargs)
        return original(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx, "Client", client)
    return configurations


@pytest.mark.parametrize("url,remote", [
    ("http://127.0.0.1:1234/v1", False), ("http://localhost:11434/v1", False),
    ("http://[::1]:8000/v1", False), ("https://inference.example/v1", True),
    ("https://192.168.1.10/v1", True),
])
def test_endpoint_classification(url, remote):
    provider = OpenAICompatibleProvider(url, "example-model")
    assert provider.is_remote is remote
    if "localhost" in url:
        assert "127.0.0.1" in provider.base_url


@pytest.mark.parametrize("url", [
    "http://remote.example/v1", "file:///private/key", "ftp://model.example/v1",
    "https://user:password@api.example/v1", "https://api.example/v1?api_key=bad",
    "https://api.example/v1#secret", "http://127.0.0.1.evil.example/v1",
    "http://localhost./v1", "http://2130706433/v1", "http://127.0.0.1%2eexample/v1",
    "http://localhost\\@example/v1", "http://localhost:0/v1", "http://localhost:bad/v1",
    "https://api.example/\nAuthorization",
])
def test_endpoint_rejects_ambiguous_or_unsafe_configuration(url):
    with pytest.raises(ValueError):
        OpenAICompatibleProvider(url, "model")


@pytest.mark.parametrize("kwargs", [
    {"model": ""}, {"timeout": 0}, {"timeout": 61}, {"timeout": float("nan")},
    {"max_tokens": 127}, {"max_tokens": 8193}, {"max_tokens": True},
    {"api_key": "header\r\ninjection"},
])
def test_request_configuration_bounds(kwargs):
    with pytest.raises(ValueError):
        OpenAICompatibleProvider("http://127.0.0.1:1234/v1", **{"model": "demo", **kwargs})


def test_openai_compatible_shape_and_transport_policy(monkeypatch):
    requests = []
    message = tool_message("finish", {"answer": "Proposal", "citations": []})

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"choices": [{"message": message, "finish_reason": "tool_calls"}]})

    configs = mock_transport(monkeypatch, handler)
    provider = OpenAICompatibleProvider("https://inference.example/v1/", "model-x", api_key="test-key")
    assert provider.complete([{"role": "user", "content": "Question"}], []) == message
    assert len(requests) == 1
    assert str(requests[0].url) == "https://inference.example/v1/chat/completions"
    assert requests[0].headers["Authorization"] == "Bearer test-key"
    body = json.loads(requests[0].content)
    assert body["model"] == "model-x" and body["stream"] is False
    assert body["max_tokens"] == 2048 and body["tool_choice"] == "auto"
    assert configs[0]["follow_redirects"] is False and configs[0]["trust_env"] is False


@pytest.mark.parametrize("response,code", [
    (httpx.Response(302, headers={"Location": "https://other.example/steal"}), "redirect_refused"),
    (httpx.Response(401, text="Bearer credential-that-must-not-be-logged"), "http_401"),
    (httpx.Response(429, text="quota"), "http_429"),
    (httpx.Response(200, content=b"not-json"), "response_invalid_json"),
    (httpx.Response(200, json=[]), "response_schema_invalid"),
    (httpx.Response(200, json={"choices": []}), "response_schema_invalid"),
    (httpx.Response(200, json={"choices": [{"message": "wrong"}]}), "response_schema_invalid"),
    (httpx.Response(200, json={"choices": [{"message": {}, "finish_reason": "length"}]}), "response_incomplete"),
    (httpx.Response(200, content=b"x" * 256001), "response_size_limit"),
])
def test_provider_failures_are_bounded_redacted_and_not_retried(monkeypatch, response, code):
    calls = []

    def handler(request):
        calls.append(request)
        return response

    mock_transport(monkeypatch, handler)
    provider = OpenAICompatibleProvider("https://inference.example/v1", "model")
    with pytest.raises(ProviderError) as error:
        provider.complete([], [])
    assert error.value.code == code and str(error.value) == code
    assert len(calls) == 1


def test_compressed_responses_are_refused_before_decode(monkeypatch):
    def handler(request):
        return httpx.Response(200, headers={"content-encoding": "gzip"}, stream=httpx.ByteStream(b"bad compressed data"))

    mock_transport(monkeypatch, handler)
    with pytest.raises(ProviderError, match="compressed_response_refused"):
        OpenAICompatibleProvider("http://127.0.0.1/v1", "model").complete([], [])


def test_request_body_cap_applies_before_transport(monkeypatch):
    def handler(request):
        pytest.fail("Oversized request should never be sent")

    mock_transport(monkeypatch, handler)
    with pytest.raises(ProviderError, match="request_size_limit"):
        OpenAICompatibleProvider("http://127.0.0.1/v1", "model").complete([{"content": "x" * 512000}], [])


def test_http_timeout_does_not_leak_sdk_exception(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("auth token secret", request=request)

    mock_transport(monkeypatch, handler)
    with pytest.raises(ProviderError, match="request_timeout") as error:
        OpenAICompatibleProvider("http://127.0.0.1/v1", "model").complete([], [])
    assert "secret" not in str(error.value)


def test_api_key_echo_is_redacted_from_run_and_database(tmp_path, monkeypatch):
    workspace = Workspace(tmp_path / "workspace")
    secret = "provider-test-secret-value"
    response = tool_message("finish", {"answer": f"Model echoed {secret}", "citations": []})
    mock_transport(monkeypatch, lambda request: httpx.Response(200, json={"choices": [{"message": response}]}))
    provider = OpenAICompatibleProvider("http://127.0.0.1/v1", "model", api_key=secret)
    run = AgentRunner(workspace, provider).run(f"Question {secret}", [])
    assert secret not in json.dumps(run)
    assert secret not in json.dumps(workspace.export_bundle())
    assert "[REDACTED]" in run["answer"]


def test_redaction_handles_nested_credential_fields():
    result = redact({"items": [{"API_KEY": "secret"}, {"Authorization": "Bearer secret"}], "text": "Bearer hidden"})
    assert result == {"items": [{"API_KEY": "[REDACTED]"}, {"Authorization": "[REDACTED]"}], "text": "Bearer [REDACTED]"}


def test_redaction_does_not_leave_changed_quote_labelled_verified(tmp_path, monkeypatch):
    workspace = Workspace(tmp_path / "workspace")
    secret = "configured-test-key"
    record = workspace.create_record("source", "Fictional secret-containing source", f"Do not publish {secret}.")
    response = tool_message("finish", {"answer": "Review this source", "citations": [{
        "record_id": record["id"], "quote": record["content"], "sha256": record["sha256"],
    }]})
    mock_transport(monkeypatch, lambda request: httpx.Response(200, json={"choices": [{"message": response}]}))
    provider = OpenAICompatibleProvider("http://127.0.0.1/v1", "model", api_key=secret)
    run = AgentRunner(workspace, provider).run("Question", [record["id"]])
    assert run["redaction_applied"] is True
    assert run["grounding"] == "unsupported" and not run["citations"]
    assert secret not in json.dumps(run)


def test_configured_credential_in_malicious_argument_keys_is_redacted(tmp_path, monkeypatch):
    workspace = Workspace(tmp_path / "workspace")
    secret = "configured-test-key"
    response = tool_message("search_records", {secret: "This malformed tool argument must not preserve the key."})
    mock_transport(monkeypatch, lambda request: httpx.Response(200, json={"choices": [{"message": response}]}))
    provider = OpenAICompatibleProvider("http://127.0.0.1/v1", "model", api_key=secret)
    run = AgentRunner(workspace, provider).run("Question", [], max_steps=1)
    assert run["status"] == "failed"
    assert secret not in json.dumps(run)
    assert secret not in json.dumps(workspace.export_bundle())
