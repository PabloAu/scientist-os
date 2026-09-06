"""Run with the wheel's isolated interpreter, from outside any source import path."""

import json
import tempfile
from io import BytesIO
from zipfile import ZipFile
from pathlib import Path

from fastapi.testclient import TestClient

import scientist_os
from scientist_os.app import create_app
from scientist_os.demo import seed_demo
from scientist_os.workspace import Workspace


def main():
    module_path = Path(scientist_os.__file__).resolve()
    if "site-packages" not in module_path.parts:
        raise RuntimeError("This check must import an installed wheel, not an editable source tree")
    with tempfile.TemporaryDirectory(prefix="scientist-os-install-") as temporary:
        workspace = Workspace(Path(temporary) / "research")
        records = seed_demo(workspace)
        app = create_app(workspace.root)
        with TestClient(app) as client:
            client.headers["x-scientist-token"] = app.state.csrf_token
            page = client.get("/")
            assert page.status_code == 200 and "Scientist OS" in page.text
            assert client.get("/static/app.js").status_code == 200
            sources = [r["id"] for r in records if r["kind"] == "source"]
            proposal = client.post("/api/agent", json={"question": "What does the example support?", "source_ids": sources}).json()
            assert proposal["status"] == "needs_review" and proposal["requests"] == 3
            draft = client.post(f"/api/runs/{proposal['id']}/draft", json={"kind": "note", "title": "Synthetic installed-wheel proposal"})
            assert draft.status_code == 200 and draft.json()["review_status"] == "unreviewed"
            data = next(r for r in records if r["kind"] == "dataset" and "readings" in r["title"])
            response = client.post("/api/analyses", json={"dataset_id": data["id"], "expected_revision": 1})
            assert response.status_code == 200, response.text
            calculation = response.json()
            assert [g["mean"] for g in calculation["result"]["groups"]] == [11, 14]
            assert client.get(f"/api/records/{calculation['output']['id']}/figure").text == calculation["output"]["content"]
            bundle = client.get("/api/export.json").json()
            assert len(bundle["records"]) == 11 and bundle["integrity_manifest"]["findings"] == []
            assert client.get("/api/export.md").status_code == 200
        reopened = Workspace(workspace.root)
        assert len(reopened.list_records()) == 11 and len(reopened.list_runs()) == 1
        authoring = create_app(Path(temporary) / "authoring")
        with TestClient(authoring) as client:
            client.headers["x-scientist-token"] = authoring.state.csrf_token
            assert client.get("/static/studio.js").status_code == 200
            seeded = client.post("/api/demo/authoring")
            assert seeded.status_code == 200, seeded.text
            items = seeded.json()["records"]
            manuscript = next(r for r in items if r["kind"] == "manuscript")
            deck = next(r for r in items if r["kind"] == "presentation")
            document = next(r for r in items if r["kind"] == "document")
            topic = next(r for r in items if r["kind"] == "discussion")
            evidence = next(r for r in items if r["kind"] == "source")
            section = manuscript["metadata"]["sections"][0]
            passage = client.post(f"/api/manuscripts/{manuscript['id']}/proposals", json={
                "expected_revision": 1, "section_id": section["id"], "start": 0, "end": 2,
                "selected_text": "We", "instruction": "Improve the scientific prose without changing the scope.",
                "source_ids": [evidence["id"]]})
            assert passage.status_code == 200, passage.text
            applied = client.post(f"/api/manuscripts/{manuscript['id']}/proposals/{passage.json()['proposal']['id']}/apply",
                                  json={"expected_revision": 1, "reviewer": "Installed-wheel test",
                                        "replacement": "Here we", "note": "Fictional engineering check only"})
            assert applied.status_code == 200 and applied.json()["manuscript"]["review_status"] == "unreviewed"
            word = client.get(f"/api/manuscripts/{manuscript['id']}/export.docx")
            assert word.status_code == 200, word.text[:100]
            with ZipFile(BytesIO(word.content)) as archive:
                assert b"Here we illustrate" in archive.read("word/document.xml")
            powerpoint = client.get(f"/api/presentations/{deck['id']}/export.pptx")
            assert powerpoint.status_code == 200, powerpoint.text[:100]
            with ZipFile(BytesIO(powerpoint.content)) as archive:
                assert "ppt/slides/slide4.xml" in archive.namelist()
            original = client.get(f"/api/library/{document['id']}/download")
            assert original.status_code == 200 and b"No real experiment" in original.content
            excerpt = client.post(f"/api/library/{document['id']}/excerpts", json={
                "expected_revision": 1, "start": 0, "end": 40,
                "selected_text": document["content"][:40], "title": "Installed-wheel excerpt"})
            assert excerpt.status_code == 201, excerpt.text
            turn = client.post(f"/api/discussions/{topic['id']}/turns", json={
                "expected_revision": 1, "question": "What should a real experiment test?",
                "source_ids": [evidence["id"]], "author": "Installed-wheel test"})
            assert turn.status_code == 200 and turn.json()["run"]["status"] == "needs_review"
            assert client.get("/api/audit").json()["integrity"] == []
    print(json.dumps({"result": "passed", "version": scientist_os.__version__, "installed_module": str(module_path),
                      "checks": ["installed static assets", "demo", "three-step agent", "unreviewed draft", "analysis",
                                 "exact figure bytes", "JSON/Markdown export", "reopen", "authoring assets",
                                 "selected passage and human apply", "DOCX/PPTX exports", "original download",
                                 "exact source excerpt", "persistent discussion"]}, indent=2))


if __name__ == "__main__":
    main()
