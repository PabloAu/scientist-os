"""Small provider contract; transport policy stays outside the model's control."""

from __future__ import annotations

import ipaddress
import json
import math
import re
from copy import deepcopy
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit


class ProviderError(RuntimeError):
    """A safe-to-log error code, without HTTP bodies, headers, or credentials."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class Provider(Protocol):
    name: str
    is_remote: bool

    def complete(self, messages: list[dict], tools: list[dict]) -> dict: ...


def redact(value: Any, secrets: tuple[str, ...] = ()) -> Any:
    """Remove configured secrets and common credential fields from persisted traces."""
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return re.sub(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", value)
    if isinstance(value, list):
        return [redact(item, secrets) for item in value]
    if isinstance(value, dict):
        return {
            redact(key, secrets): "[REDACTED]"
            if re.sub(r"[^a-z]", "", str(key).lower())
            in {"apikey", "authorization", "password", "secret", "accesstoken", "refreshtoken"}
            else redact(item, secrets)
            for key, item in value.items()
        }
    return value


def redact_run(run: dict, sanitizer: Any = redact) -> dict:
    """Do not leave a modified quotation labelled as verified after redaction."""
    safe = sanitizer(run)
    if safe != run:
        safe["redaction_applied"] = True
    original_citations = run.get("citations", [])
    safe_citations = safe.get("citations", [])
    if safe_citations != original_citations:
        safe["citations"] = [safe_citation for original, safe_citation in zip(original_citations, safe_citations)
                             if original == safe_citation]
        safe.setdefault("warnings", []).append("Credential redaction removed altered quotations from verified citations. Traces may also be redacted.")
        safe["grounding"] = "verified_quotes" if safe["citations"] else "unsupported"
        if not safe["citations"] and safe.get("status") == "needs_review":
            safe["answer"] = "Unsupported proposal — no verified source quotations remain after redaction.\n\n" + safe["answer"]
    return safe


def tool_message(name: str, arguments: dict, call_id: str = "call_1") -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{"id": call_id, "type": "function", "function": {
            "name": name, "arguments": json.dumps(arguments, ensure_ascii=False)
        }}],
    }


class DemoProvider:
    """Deterministic search/read/finish fixture. This is not a language model."""

    name = "deterministic-demo"
    model = "none"
    is_remote = False

    def complete(self, messages: list[dict], tools: list[dict]) -> dict:
        del tools
        request = json.loads(next(m["content"] for m in messages if m["role"] == "user"))
        observations = [m for m in messages if m["role"] == "tool"]
        selected = request["selected_sources"]
        if not selected:
            return tool_message("finish", {
                "answer": "Deterministic demo: no sources were selected; no scientific answer is supported.",
                "citations": [],
            })
        if not observations:
            terms = re.findall(r"\w+", request["question"])
            return tool_message("search_records", {"query": " ".join(terms[:8]) or "source"}, "demo_search")
        if len(observations) == 1:
            result = json.loads(observations[-1]["content"])
            hits = result.get("records", [])
            record_id = hits[0]["record_id"] if hits else selected[0]["record_id"]
            return tool_message("read_record", {"record_id": record_id}, "demo_read")
        result = json.loads(observations[-1]["content"])
        record = result.get("record")
        if not record:
            return tool_message("finish", {
                "answer": "Deterministic demo: a source could not be read; please review the trace.", "citations": []
            }, "demo_finish")
        quote = record["content"][:300]
        citations = [{"record_id": record["record_id"], "quote": quote, "sha256": record["sha256"]}] if quote else []
        return tool_message("finish", {
            "answer": (
                "Deterministic demo — no LLM inference was performed.\n\n"
                f"Requested task: {request['task']}. Selected evidence excerpt:\n\n{quote}\n\n"
                "Human review: check whether this excerpt answers the question, establish independent "
                "replication and measurement units, and inspect uncertainty before drawing conclusions. "
                "Connect a tool-capable model to generate a tailored proposal."
            ),
            "citations": citations,
        }, "demo_finish")


class ScriptedProvider:
    """Explicit test double; never presented as a live model."""

    name = "scripted-test-double"
    model = "none"

    def __init__(self, responses: list[dict | Exception], *, is_remote: bool = False) -> None:
        self.responses = list(responses)
        self.is_remote = is_remote
        self.calls: list[dict] = []

    def complete(self, messages: list[dict], tools: list[dict]) -> dict:
        self.calls.append(deepcopy({"messages": messages, "tools": tools}))
        if not self.responses:
            raise ProviderError("script_exhausted")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return deepcopy(response)


class OpenAICompatibleProvider:
    """Synchronous, single-request Chat Completions adapter with no retries.

    Source disclosure is enforced by AgentRunner, not by calling complete directly.
    Only trusted local application code should instantiate provider adapters.
    """

    name = "openai-compatible"
    MAX_REQUEST_BYTES = 512_000
    MAX_RESPONSE_BYTES = 256_000

    def __init__(
        self, base_url: str, model: str, api_key: str | None = None,
        timeout: float = 30, max_tokens: int = 2048,
    ) -> None:
        if not isinstance(base_url, str) or not 1 <= len(base_url) <= 2000:
            raise ValueError("A bounded endpoint URL is required")
        if any(ord(char) <= 32 or ord(char) == 127 for char in base_url) or "\\" in base_url:
            raise ValueError("Endpoint URL contains forbidden characters")
        parts = urlsplit(base_url)
        try:
            port = parts.port
        except ValueError as exc:
            raise ValueError("Invalid endpoint port") from exc
        if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username is not None or parts.password is not None:
            raise ValueError("Endpoint must be HTTP(S) without embedded credentials")
        if parts.query or parts.fragment or "%" in parts.netloc or port == 0:
            raise ValueError("Endpoint cannot contain query, fragment, or encoded host")
        hostname = parts.hostname.lower()
        try:
            loopback = ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            loopback = hostname == "localhost"
        if not loopback and parts.scheme != "https":
            raise ValueError("Non-loopback endpoints require HTTPS")
        if not isinstance(model, str) or not model.strip() or len(model) > 200:
            raise ValueError("A model identifier of 1–200 characters is required")
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or not 1 <= timeout <= 60:
            raise ValueError("timeout must be between 1 and 60 seconds")
        if type(max_tokens) is not int or not 128 <= max_tokens <= 8192:
            raise ValueError("max_tokens must be between 128 and 8192")
        if api_key is not None and (not isinstance(api_key, str) or len(api_key) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in api_key)):
            raise ValueError("API key must be bounded printable ASCII without whitespace")
        # localhost is normalized to a literal address so DNS cannot redirect its local policy.
        host = "127.0.0.1" if hostname == "localhost" else hostname
        authority = f"[{host}]" if ":" in host else host
        if port:
            authority += f":{port}"
        self.base_url = urlunsplit((parts.scheme, authority, parts.path.rstrip("/"), "", ""))
        self.model = model.strip()
        self.is_remote = not loopback
        self.timeout = float(timeout)
        self.max_tokens = max_tokens
        self._api_key = api_key

    def redact(self, value: Any) -> Any:
        return redact(value, (self._api_key,) if self._api_key else ())

    def complete(self, messages: list[dict], tools: list[dict]) -> dict:
        import httpx

        payload = {
            "model": self.model, "messages": messages, "tools": tools,
            "tool_choice": "auto", "max_tokens": self.max_tokens, "stream": False,
        }
        try:
            body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ProviderError("request_invalid_json") from exc
        if len(body) > self.MAX_REQUEST_BYTES:
            raise ProviderError("request_size_limit")
        headers = {"Content-Type": "application/json", "Accept": "application/json", "Accept-Encoding": "identity"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        # No environment proxies, redirects, retry loop, or content in error messages.
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=False, trust_env=False) as client:
                with client.stream("POST", self.base_url + "/chat/completions", content=body, headers=headers) as response:
                    if 300 <= response.status_code < 400:
                        raise ProviderError("redirect_refused")
                    if not 200 <= response.status_code < 300:
                        raise ProviderError(f"http_{response.status_code}")
                    # Refuse compressed responses to bound decompression memory as well as bytes.
                    if response.headers.get("content-encoding", "identity").lower() not in {"identity", ""}:
                        raise ProviderError("compressed_response_refused")
                    data = bytearray()
                    for chunk in response.iter_bytes(chunk_size=8192):
                        data.extend(chunk)
                        if len(data) > self.MAX_RESPONSE_BYTES:
                            raise ProviderError("response_size_limit")
            decoded = json.loads(data)
            choices = decoded.get("choices") if isinstance(decoded, dict) else None
            if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
                raise ProviderError("response_schema_invalid")
            choice = choices[0]
            if choice.get("finish_reason") in {"length", "content_filter"}:
                raise ProviderError("response_incomplete")
            message = choice.get("message")
            if not isinstance(message, dict):
                raise ProviderError("response_schema_invalid")
            return message
        except ProviderError:
            raise
        except httpx.TimeoutException:
            raise ProviderError("request_timeout") from None
        except httpx.HTTPError:
            raise ProviderError("transport_error") from None
        except (ValueError, TypeError, KeyError, UnicodeError):
            raise ProviderError("response_invalid_json") from None
