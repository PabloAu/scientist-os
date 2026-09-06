"""Exercise scientist-facing HTTP workflows and local browser boundaries."""

import json
from xml.etree import ElementTree

from fastapi.testclient import TestClient
import pytest

from scientist_os.app import MAX_REQUEST, create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / "workspace")
    with TestClient(app, raise_server_exceptions=False) as session:
        session.headers["x-scientist-token"] = app.state.csrf_token
        yield session


def records(client):
    response = client.get("/api/state")
    assert response.status_code == 200, response.text
    return response.json()["records"]


def create(client, kind="dataset", title="Synthetic input", content="group,day,signal\ncontrol,A,1\ncontrol,B,3\n", **extra):
    response = client.post("/api/records", json={"kind": kind, "title": title, "content": content, **extra})
    assert response.status_code == 201, response.text
    return response.json()


def analyze(client, dataset, **extra):
    response = client.post("/api/analyses", json={"dataset_id": dataset["id"], **extra})
    assert response.status_code == 200, response.text
    return response.json()


def review(client, record, **extra):
    response = client.post(f"/api/records/{record['id']}/review", json={
        "expected_revision": record["revision"], "decision": "approved", "reviewer": "Dr Example",
        "note": "Reviewed the synthetic calculation.", **extra,
    })
    assert response.status_code == 200, response.text
    return response.json()


def snapshot(client):
    return records(client), client.get("/api/events").json()


def test_empty_app_initializes_and_reopens_without_changing_records(client):
    state = client.get("/api/state").json()
    assert state["records"] == state["runs"] == []
    assert state["mode"] == "single-user local"
    assert len(state["stages"]) >= 10
    created = create(client, kind="note", title="Saved research question", content="What should we measure?")
    with TestClient(create_app(client.app.state.workspace.root)) as reopened:
        assert reopened.get("/api/state").json()["records"] == [created]


def test_browser_page_receives_token_and_security_headers(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "__CSRF_TOKEN__" not in response.text
    assert client.app.state.csrf_token in response.text
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_full_synthetic_summary_review_edit_and_exports(client):
    seeded = client.post("/api/demo")
    assert seeded.status_code == 200, seeded.text
    demo = seeded.json()["records"]
    assert len(demo) >= 8
    assert all(record["metadata"]["synthetic"] is True for record in demo)
    dataset = next(record for record in demo if record["kind"] == "dataset" and "readings" in record["title"])
    result = analyze(client, dataset)
    assert result["result"]["rows_total"] == 12
    groups = {group["group"]: group for group in result["result"]["groups"]}
    assert groups["control"]["mean"] == 11
    assert groups["treatment"]["mean"] == 14
    assert groups["control"]["n_units"] == groups["treatment"]["n_units"] == 3
    figure = client.get(f"/api/records/{result['output']['id']}/figure")
    assert figure.status_code == 200
    assert figure.headers["content-type"].startswith("image/svg+xml")
    assert ElementTree.fromstring(figure.text).tag.endswith("svg")
    approved = review(client, result["analysis"])
    assert approved["review_status"] == "approved"
    correction = client.patch(f"/api/records/{dataset['id']}", json={
        "expected_revision": dataset["revision"], "content": dataset["content"].replace("control,C1,9", "control,C1,7"),
    })
    assert correction.status_code == 200
    invalidated = client.get(f"/api/records/{approved['id']}").json()
    assert invalidated["review_status"] == "unreviewed"
    assert invalidated["revision"] > approved["revision"]
    integrity = client.get("/api/audit").json()["integrity"]
    assert any(finding["code"] == "stale_input_revision" for finding in integrity)
    exported = client.get("/api/export.json")
    assert exported.status_code == 200
    assert "attachment" in exported.headers["content-disposition"]
    bundle = exported.json()
    assert len(bundle["records"]) == len(demo) + 2
    assert bundle["events"] and bundle["integrity_manifest"]["bundle_sha256"]
    markdown = client.get("/api/export.md")
    assert markdown.status_code == 200
    assert "Scientist OS research handoff" in markdown.text
    assert approved["id"] in markdown.text
    assert "unreviewed" in markdown.text


def test_loading_demo_into_nonempty_workspace_is_rejected_without_changes(client):
    create(client, kind="note")
    before = snapshot(client)
    response = client.post("/api/demo")
    assert response.status_code == 400
    assert snapshot(client) == before


def test_search_and_human_audit_are_read_only(client):
    note = create(client, kind="source", title="Evidence", content="Exact observed signal.")
    before = snapshot(client)
    result = client.get("/api/search", params={"q": "signal"})
    assert result.status_code == 200
    assert result.json()[0]["record_id"] == note["id"]
    assert result.json()[0]["quote"] in note["content"]
    audit = client.get("/api/audit").json()
    assert audit["integrity"] == []
    assert audit["scientific_screening"]
    assert snapshot(client) == before


@pytest.mark.parametrize("headers", [
    {"x-scientist-token": ""}, {"x-scientist-token": "wrong"},
    {"origin": "https://attacker.example"}, {"origin": "null"},
    {"sec-fetch-site": "cross-site"}, {"host": "attacker.example"},
    {"host": "127.0.0.1.attacker.example"},
])
def test_cross_origin_and_missing_token_writes_are_blocked(client, headers):
    before = snapshot(client)
    response = client.post("/api/records", headers=headers, json={"kind": "note", "title": "Must not save"})
    assert response.status_code == 403, response.text
    assert snapshot(client) == before


@pytest.mark.parametrize("host", ["[", "[::1", "localhost/attacker", "user@localhost", "localhost:invalid"])
def test_malformed_host_authorities_are_rejected_without_server_errors(client, host):
    response = client.get("/api/state", headers={"host": host})
    assert response.status_code == 403, (host, response.status_code, response.text)


def test_same_origin_authenticated_write_is_accepted(client):
    response = client.post("/api/records", headers={"origin": "http://testserver", "sec-fetch-site": "same-origin"},
                           json={"kind": "note", "title": "Allowed local write"})
    assert response.status_code == 201, response.text


def test_oversized_and_chunked_bodies_are_rejected_before_mutation(client):
    response = client.post("/api/records", content=b"x" * (MAX_REQUEST + 1), headers={"content-type": "application/json"})
    assert response.status_code == 413, response.text

    def chunks():
        yield b"x" * (MAX_REQUEST // 2)
        yield b"x" * (MAX_REQUEST // 2 + 1)

    streamed = client.post("/api/records", content=chunks(), headers={"content-type": "application/json"})
    assert streamed.status_code == 413, streamed.text
    assert snapshot(client) == ([], [])


def test_extra_fields_and_malformed_json_are_rejected(client):
    unknown = client.post("/api/records", json={"kind": "note", "title": "No", "review_status": "approved"})
    assert unknown.status_code == 422
    malformed = client.post("/api/records", content='{"kind":', headers={"content-type": "application/json"})
    assert malformed.status_code == 422
    assert snapshot(client) == ([], [])


@pytest.mark.parametrize("bad_id", ["source_bad", "source_..", "not-an-id"])
def test_malformed_record_ids_are_controlled_errors(client, bad_id):
    assert client.get(f"/api/records/{bad_id}").status_code == 400
    assert client.get(f"/api/records/{bad_id}/figure").status_code == 400
    assert client.get("/api/records/source_" + "a" * 32).status_code == 404


def test_http_rejects_boolean_revisions_without_mutation(client):
    note = create(client, kind="note")
    before = snapshot(client)
    response = client.patch(f"/api/records/{note['id']}", json={"expected_revision": True, "content": "Must not save"})
    assert response.status_code in {400, 422}, response.text
    assert snapshot(client) == before


@pytest.mark.parametrize("spec", [
    {"method": "unknown"}, {"value_column": "missing"}, {"group_column": "signal"},
    {"unit_column": "unknown"}, {"method": "meta"},
    {"method": "meta", "comparability_confirmed": True, "effect_measure": " "},
])
def test_invalid_analysis_spec_preserves_workspace(client, spec):
    dataset = create(client)
    before = snapshot(client)
    response = client.post("/api/analyses", json={"dataset_id": dataset["id"], **spec})
    assert response.status_code == 400, response.text
    assert snapshot(client) == before


@pytest.mark.parametrize("text", [
    "group,day,signal\ncontrol,A,bad\n", "group,day,signal\ncontrol,A,nan\n",
    "group,day,signal\ncontrol,A,1\ntreatment,A,3\n",
    "group,day,signal\ncontrol,A,1,unexpected\n", "group,day,signal,signal\ncontrol,A,1,2\n",
], ids=["bad-value", "nonfinite", "overlapping-unit", "extra-cell", "duplicate-header"])
def test_malformed_summary_data_does_not_create_partial_analysis(client, text):
    dataset = create(client, content=text)
    before = snapshot(client)
    response = client.post("/api/analyses", json={"dataset_id": dataset["id"]})
    assert response.status_code == 400, response.text
    assert snapshot(client) == before


@pytest.mark.parametrize("text", [
    "study_id,effect,standard_error\nA,0.2,0.1,unexpected\nB,0.4,0.2,unexpected\n",
    "study_id,effect,effect,standard_error\nA,999,0.2,0.1\nB,999,0.4,0.2\n",
    "study_id,effect,standard_error\nA,NaN,0.1\nB,0.4,0.2\n",
    "study_id,effect,standard_error\nA,0.2,0\nB,0.4,0.2\n",
    "study_id,effect,standard_error\nA,0.2,0.1\nA,0.4,0.2\n",
], ids=["extra-cell", "duplicate-header", "nonfinite", "zero-error", "duplicate-study"])
def test_malformed_meta_csv_has_no_silent_column_discard_or_partial_writes(client, text):
    dataset = create(client, content=text)
    before = snapshot(client)
    response = client.post("/api/analyses", json={"dataset_id": dataset["id"], "method": "meta",
                           "comparability_confirmed": True, "effect_measure": "Common synthetic effect"})
    assert response.status_code == 400, response.text[:500]
    assert snapshot(client) == before


def test_comparable_meta_analysis_has_lineage_and_safe_forest(client):
    dataset = create(client, content="study_id,effect,standard_error\nA,0.2,0.1\nB,0.4,0.2\n")
    result = analyze(client, dataset, method="meta", comparability_confirmed=True, effect_measure="Synthetic standardized effect")
    assert result["result"]["n_studies"] == 2
    assert result["analysis"]["metadata"]["input_revisions"] == {dataset["id"]: 1}
    assert result["analysis"]["metadata"]["input_hashes"] == {dataset["id"]: dataset["sha256"]}
    figure = client.get(f"/api/records/{result['output']['id']}/figure")
    assert figure.status_code == 200
    assert "95%" in figure.text


@pytest.mark.parametrize("text", [
    "group,day,signal\ncontrol,A,\ncontrol,B,\n",
    "group,day,signal\n" + "".join(f"g{i},day{i},1\n" for i in range(201)),
], ids=["all-missing", "too-many-groups"])
def test_failed_figure_generation_does_not_leave_partial_analysis(client, text):
    dataset = create(client, content=text)
    before = snapshot(client)
    response = client.post("/api/analyses", json={"dataset_id": dataset["id"]})
    assert response.status_code == 400, response.text
    assert snapshot(client) == before


def test_whitespace_reviewer_cannot_create_review_or_workflow_partial_write(client):
    note = create(client, kind="note")
    before = snapshot(client)
    response = client.post(f"/api/records/{note['id']}/review", json={
        "expected_revision": note["revision"], "decision": "approved", "reviewer": "  ", "note": "Reviewed",
    })
    assert response.status_code in {400, 422}
    assert snapshot(client) == before
    stage = client.get("/api/state").json()["stages"][0]
    gate = client.post(f"/api/workflow/{stage['id']}", json={
        "reviewer": "  ", "note": "Reviewed all checkpoints", "checked": stage["checks"], "links": [note["id"]],
    })
    assert gate.status_code in {400, 422}, gate.text
    assert snapshot(client) == before


def test_workflow_requires_a_nonblank_decision_note_and_all_checks(client):
    stage = client.get("/api/state").json()["stages"][0]
    before = snapshot(client)
    incomplete = client.post(f"/api/workflow/{stage['id']}", json={
        "reviewer": "Dr Example", "note": "Reviewed", "checked": stage["checks"][:1],
    })
    assert incomplete.status_code == 400
    blank = client.post(f"/api/workflow/{stage['id']}", json={
        "reviewer": "Dr Example", "note": " \n ", "checked": stage["checks"],
    })
    assert blank.status_code in {400, 422}, blank.text
    assert snapshot(client) == before


def test_valid_workflow_gate_records_named_human_decision(client):
    stage = client.get("/api/state").json()["stages"][0]
    gate = client.post(f"/api/workflow/{stage['id']}", json={
        "reviewer": "Dr Example", "note": "Question and decision owner documented.", "checked": stage["checks"],
    })
    assert gate.status_code == 200, gate.text
    record = gate.json()
    assert record["kind"] == "decision"
    assert record["review_status"] == "approved"
    assert record["metadata"]["reviewer"] == "Dr Example"
    assert client.get("/api/events").json()[-1]["data"]["reviewer"] == "Dr Example"


def test_figure_endpoint_never_serves_user_supplied_svg_script(client):
    dataset = create(client, title='Title <script>alert("title")</script>',
                     content='group,day,signal\n"<script>alert(1)</script>",A,1\n"<script>alert(1)</script>",B,3\n')
    result = analyze(client, dataset)
    malicious = create(client, kind="output", title="Imported SVG",
                       content='<svg xmlns="http://www.w3.org/2000/svg" onload="alert(2)"><script>alert(3)</script></svg>',
                       metadata={"format": "svg"}, links=[result["analysis"]["id"]])
    response = client.get(f"/api/records/{malicious['id']}/figure")
    assert response.status_code == 200
    root = ElementTree.fromstring(response.text)
    assert all(not node.tag.endswith("script") for node in root.iter())
    assert all(not any(key.lower().startswith("on") for key in node.attrib) for node in root.iter())
    assert "<script>" not in response.text
    assert "alert(2)" not in response.text
    assert "&lt;script&gt;" in response.text


def test_figure_requires_reproducible_numeric_analysis(client):
    imported = create(client, kind="output", title="Imported unsafe SVG", content="<svg><script>alert(1)</script></svg>",
                      metadata={"format": "svg"})
    response = client.get(f"/api/records/{imported['id']}/figure")
    assert response.status_code == 400
    assert "<script>" not in response.text
    malformed = create(client, kind="analysis", title="Malformed numeric result",
                       metadata={"result": {"type": "csv_summary", "groups": [{"mean": "<script>alert(1)</script>"}]}})
    output = create(client, kind="output", metadata={"format": "svg"}, links=[malformed["id"]])
    result = client.get(f"/api/records/{output['id']}/figure")
    assert result.status_code == 400


def test_stale_figure_never_silently_renders_changed_parent_numbers(client):
    dataset = create(client)
    calculated = analyze(client, dataset)
    analysis = calculated["analysis"]
    metadata = json.loads(json.dumps(analysis["metadata"]))
    metadata["result"]["groups"][0]["mean"] = 999
    changed = client.patch(f"/api/records/{analysis['id']}", json={"expected_revision": analysis["revision"], "metadata": metadata})
    assert changed.status_code == 200, changed.text
    response = client.get(f"/api/records/{calculated['output']['id']}/figure")
    assert response.status_code == 409, response.text
