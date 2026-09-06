import httpx
import pytest

from scientist_os.literature import search_literature


def transport(payload, status=200):
    def handle(request):
        assert request.url.host == "api.crossref.org"
        assert request.url.path == "/works"
        assert request.url.params["query.bibliographic"] == "microscopy controls"
        assert request.url.params["rows"] == "5"
        assert not request.content
        return httpx.Response(status, json=payload)
    return httpx.MockTransport(handle)


def test_discovery_normalizes_metadata_without_claiming_full_text():
    result = search_literature("microscopy controls", transport=transport({"message": {"items": [{
        "title": ["Testing <controls>"], "DOI": "10.1234/example",
        "author": [{"given": "A", "family": "Researcher"}], "published": {"date-parts": [[2024, 1]]},
        "abstract": "<p>An <i>abstract</i> only.</p>", "container-title": ["Test Journal"],
        "URL": "http://127.0.0.1/private"}]}}))
    item = result["items"][0]
    assert item["url"] == "https://doi.org/10.1234/example"
    assert item["year"] == 2024 and item["authors"] == ["A Researcher"]
    assert item["abstract"] == "An  abstract  only."
    assert item["full_text_ids"] == [] and "not full-text" in result["notice"]


@pytest.mark.parametrize("query", ["", "a", "two\nlines", "x" * 301, "bad\ud800"])
def test_bad_query_never_calls_network(query):
    def fail(_):
        pytest.fail("Network must not run for invalid query")
    with pytest.raises(ValueError):
        search_literature(query, transport=httpx.MockTransport(fail))


@pytest.mark.parametrize("payload", [[], {"message": []}, {"message": {"items": "not items"}}])
def test_malformed_response_is_user_readable(payload):
    with pytest.raises(ValueError):
        search_literature("microscopy controls", transport=transport(payload))


def test_redirect_not_followed():
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(302, headers={"Location": "http://127.0.0.1/private"})
    with pytest.raises(ValueError, match="unavailable"):
        search_literature("microscopy controls", transport=httpx.MockTransport(handle))
    assert len(calls) == 1


def test_entity_xml_and_unusable_entries_not_treated_as_evidence():
    result = search_literature("microscopy controls", transport=transport({"message": {"items": [
        {"title": ["Bad"], "DOI": "bad"},
        {"title": ["Metadata"], "DOI": "10.1234/example", "abstract": '<!DOCTYPE x [<!ENTITY x SYSTEM "file:///secret">]><p>&x;</p>'}]
    }}))
    assert len(result["items"]) == 1 and result["items"][0]["abstract"] == ""
