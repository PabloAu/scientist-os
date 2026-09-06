"""Run with the wheel's isolated interpreter, from outside any source import path."""

import json
import tempfile
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
    print(json.dumps({"result": "passed", "version": scientist_os.__version__, "installed_module": str(module_path),
                      "checks": ["installed static assets", "demo", "three-step agent", "unreviewed draft", "analysis",
                                 "exact figure bytes", "JSON/Markdown export", "reopen"]}, indent=2))


if __name__ == "__main__":
    main()
