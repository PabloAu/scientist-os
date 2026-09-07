import hashlib

import pytest

from scientist_os.governance import Governance
from scientist_os.workspace import Workspace


def test_review_baseline_survives_revision_and_detects_tampering(tmp_path):
    workspace = Workspace(tmp_path)
    original = workspace.create_record("manuscript", "Draft", "Bounded claim")
    file = tmp_path / "submitted.txt"
    file.write_text("exact submitted artifact", encoding="utf-8")
    governance = Governance(workspace)
    review = governance.start_review("Round 1", [original["id"]], [file.name], round_label="mock R1")
    workspace.update_record(original["id"], expected_revision=1, content="Revised bounded claim")
    saved = workspace.get_record(review["id"])["metadata"]
    assert saved["baseline_records"][0]["content"] == "Bounded claim"
    snapshot = tmp_path / saved["files"][0]["snapshot"]
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == saved["files"][0]["sha256"]
    snapshot.write_text("changed", encoding="utf-8")
    assert any(f["code"] == "baseline_changed" for f in governance.check_review(review["id"])["findings"])


def test_material_scientific_fix_requires_decision(tmp_path):
    governance = Governance(Workspace(tmp_path))
    problem = governance.capture_problem({"title": "Exclusion policy", "observed": "Selective filtering",
        "expected": "Declared exclusions", "reproduction": "Case A", "classification": "material_scientific",
        "owner": "scientist", "next_check": "Revisit analysis plan"})
    resolution = {"cause": "Undeclared rule", "fix": "Proposed rule", "representative_verification": "Case A",
                  "procedure": "analysis", "version": "test", "applicability_limits": "fixture",
                  "attributed_to": "agent"}
    with pytest.raises(ValueError, match="scientist decision"):
        governance.resolve_problem(problem["id"], 1, resolution)


def test_review_rejects_outside_workspace_file(tmp_path):
    workspace = Workspace(tmp_path / "project")
    note = workspace.create_record("note", "Scope", "Fictional")
    (tmp_path / "secret.txt").write_text("private")
    with pytest.raises(ValueError, match="inside"):
        Governance(workspace).start_review("Round", [note["id"]], ["../secret.txt"], round_label="mock")


def test_review_response_is_bound_to_accepted_evidence_revision(tmp_path):
    workspace = Workspace(tmp_path)
    source = workspace.create_record("source", "Evidence", "Positive")
    (tmp_path / "draft.txt").write_text("Original")
    governance = Governance(workspace)
    review = governance.start_review("Mock", [source["id"]], ["draft.txt"], round_label="R1")
    governance.review_request(review["id"], review["revision"], {
        "request_id": "R1-1", "verbatim": "Clarify", "source_locator": "Mock review line1",
        "disposition": "clarify", "rationale": "Evidence supports bounded claim",
        "inventory_consulted": "All fixture records", "needs_experiment": False,
        "evidence_ids": [source["id"]], "response": "Clarified", "current_locator": "Results",
        "change_summary": "Bounded claim"})
    assert governance.check_review(review["id"])["mechanically_complete"]
    workspace.update_record(source["id"], expected_revision=1, content="Negative")
    result = governance.check_review(review["id"])
    assert not result["mechanically_complete"]
    assert {f["code"] for f in result["findings"]} == {"stale_request_evidence"}
