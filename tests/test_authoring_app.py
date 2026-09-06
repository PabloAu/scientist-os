"""Scientist-facing authoring flow through the same HTTP interface as the browser."""

from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
import pytest

from scientist_os.app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path)
    with TestClient(app, raise_server_exceptions=False) as client:
        client.headers["x-scientist-token"] = app.state.csrf_token
        yield client


def post(client, path, body):
    response = client.post("/api/" + path, json=body)
    assert response.is_success, response.text
    return response.json()


def test_complete_authoring_edit_export_and_discussion(client):
    response = client.post("/api/demo/authoring")
    assert response.status_code == 200, response.text
    records = response.json()["records"]
    manuscript = next(r for r in records if r["kind"] == "manuscript")
    deck = next(r for r in records if r["kind"] == "presentation")
    document = next(r for r in records if r["kind"] == "document")
    discussion = next(r for r in records if r["kind"] == "discussion")
    source = next(r for r in records if r["kind"] == "source")
    section = manuscript["metadata"]["sections"][0]
    proposal = post(client, f"manuscripts/{manuscript['id']}/proposals", {
        "expected_revision": 1, "section_id": section["id"], "start": 0, "end": 2,
        "selected_text": "We", "instruction": "Check this passage against the selected teaching evidence.",
        "source_ids": [source["id"]]})
    assert proposal["run"]["status"] == "needs_review"
    assert client.get(f"/api/records/{manuscript['id']}").json()["revision"] == 1
    applied = post(client, f"manuscripts/{manuscript['id']}/proposals/{proposal['proposal']['id']}/apply", {
        "expected_revision": 1, "reviewer": "Agent-operated interface test",
        "replacement": "Here we", "note": "Fictional edit-flow verification, not scientific review."})
    assert applied["manuscript"]["metadata"]["sections"][0]["text"].startswith("Here we illustrate")
    assert applied["manuscript"]["review_status"] == "unreviewed"
    replay = client.post(f"/api/manuscripts/{manuscript['id']}/proposals/{proposal['proposal']['id']}/apply",
                         json={"expected_revision": 1, "reviewer": "Test"})
    assert replay.status_code == 409
    word = client.get(f"/api/manuscripts/{manuscript['id']}/export.docx")
    assert word.status_code == 200, word.text[:100]
    with ZipFile(BytesIO(word.content)) as archive:
        document_xml = archive.read("word/document.xml").decode()
        assert "Here we illustrate" in document_xml and "Supplementary methods" in document_xml
        assert "Fictional calibration notes" in document_xml
        assert any(n.startswith("word/media/") for n in archive.namelist())
    powerpoint = client.get(f"/api/presentations/{deck['id']}/export.pptx")
    assert powerpoint.status_code == 200, powerpoint.text[:100]
    with ZipFile(BytesIO(powerpoint.content)) as archive:
        slides = [n for n in archive.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
        assert len(slides) == 4
        assert b"descriptive difference" in archive.read("ppt/slides/slide3.xml")
    html = client.get(f"/api/manuscripts/{manuscript['id']}/export.html")
    assert html.status_code == 200 and "attachment" in html.headers["content-disposition"]
    original = client.get(f"/api/library/{document['id']}/download")
    assert original.status_code == 200 and b"No real experiment" in original.content
    assert "attachment" in original.headers["content-disposition"]
    turn = post(client, f"discussions/{discussion['id']}/turns", {"expected_revision": 1,
        "question": "What controls should a real experiment consider?", "source_ids": [source["id"]],
        "author": "Agent-operated interface test"})
    assert turn["discussion"]["metadata"]["turns"][0]["run_id"] == turn["run"]["id"]
    assert turn["discussion"]["review_status"] == "unreviewed"
    assert client.get("/api/audit").json()["integrity"] == []


def test_library_preserves_originals_and_rejects_cross_origin(client):
    response = client.post("/api/library/import?filename=proposal.md&category=proposal",
                           content=b"# Proposal\nAn untested idea.", headers={"content-type": "application/octet-stream"})
    assert response.status_code == 201, response.text
    record = response.json()
    assert record["metadata"]["external_allowed"] is False
    assert record["metadata"]["category"] == "proposal"
    assert client.get(f"/api/library/{record['id']}/download").content == b"# Proposal\nAn untested idea."
    refused = client.post("/api/library/import?filename=proposal.md", content=b"secret",
                          headers={"content-type": "application/octet-stream", "origin": "https://attacker.example"})
    assert refused.status_code == 403
    assert len(client.get("/api/state").json()["records"]) == 1


def test_references_support_editing_and_null_year(client):
    reference = post(client, "references", {"title": "Bibliographic example", "year": 2020})
    response = client.patch(f"/api/references/{reference['id']}",
                            json={"expected_revision": 1, "year": None, "authors": ["Example author"]})
    assert response.status_code == 200 and response.json()["metadata"]["year"] is None
    assert "does not establish" in response.json()["content"]
    bad = client.post("/api/references", json={"title": "Bad", "year": True})
    assert bad.status_code == 422


def test_editing_data_blocks_existing_manuscript_and_slide_exports(client):
    records = client.post("/api/demo/authoring").json()["records"]
    data = next(r for r in records if r["kind"] == "dataset" and "readings" in r["title"])
    client.patch(f"/api/records/{data['id']}", json={"expected_revision": 1, "content": data["content"] + "control,C4,100\n"})
    manuscript = next(r for r in records if r["kind"] == "manuscript")
    deck = next(r for r in records if r["kind"] == "presentation")
    assert client.get(f"/api/manuscripts/{manuscript['id']}/export.docx").status_code == 409
    assert client.get(f"/api/presentations/{deck['id']}/export.pptx").status_code == 409
