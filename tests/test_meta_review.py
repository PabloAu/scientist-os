"""Controlled selection/extraction/synthesis checks on transparently invented reports."""

from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from scientist_os.meta_review import MetaReview
from scientist_os.workspace import Workspace


FIXTURE = Path(__file__).parents[1] / "examples" / "pipelines" / "meta_fixture.py"
loader = importlib.util.spec_from_file_location("fictional_meta", FIXTURE)
fixture_module = importlib.util.module_from_spec(loader)
loader.loader.exec_module(fixture_module)
DECISION = {"actor": "development agent", "actor_type": "agent", "kind": "fixture_authorization",
            "statement": "Freeze the invented arithmetic exercise, not a real scientific conclusion",
            "basis": "User authorization to implement and verify fictional examples"}


@pytest.fixture
def review(tmp_path):
    workspace = Workspace(tmp_path / "review")
    service = MetaReview(workspace)
    spec = fixture_module.create_spec(workspace)
    record = service.create(spec)
    return workspace, service, record, spec


def test_complete_traceable_review_computes_known_meta_and_sensitivity(review):
    workspace, service, record, spec = review
    check = service.check(record["id"])
    assert check["ready_to_freeze"], check["issues"]
    assert check["flow"] == {"registered": 5, "included": 3, "excluded": 1, "duplicate": 1, "pending": 0}
    frozen = service.freeze(record["id"], DECISION)
    assert frozen["metadata"]["scientific_approval"] is False
    result = service.synthesize(record["id"])
    assert result["result"]["estimate"] == 2
    assert result["result"]["Q"] == 8
    assert result["result"]["I2"] == 75
    assert result["result"]["tau2"] == 3
    assert result["result"]["standard_error"] == pytest.approx(math.sqrt(4 / 3))
    assert len(result["sensitivity"]) == 5
    loo = [scenario for scenario in result["sensitivity"] if scenario["name"] == "Leave out fictional-C"][0]
    assert loo["result"]["estimate"] == 1
    assert result["analysis"]["review_status"] == "unreviewed"
    assert workspace.validate_current(result["figure"]["id"])
    from scientist_os.publishing import publication_figure
    assert publication_figure(workspace, result["figure"]["id"]).startswith(b"\x89PNG")
    for name in ("forest.svg", "sensitivity.svg"):
        ET.parse(result["files"][name]["path"])
    csv = Path(result["files"]["selection.csv"]["path"]).read_text()
    assert "fictional-incompatible" in csv and "duplicate" in csv
    stored = json.loads(Path(result["files"]["review_snapshot.json"]["path"]).read_text())
    assert stored["metadata"]["freeze_decision"]["actor_type"] == "agent"


def test_empty_review_guides_completion_instead_of_fake_synthesis(tmp_path):
    service = MetaReview(Workspace(tmp_path))
    record = service.create({"question": "What evidence would answer my question?"})
    check = service.check(record["id"])
    assert not check["ready_to_freeze"]
    codes = {issue["code"] for issue in check["issues"]}
    assert {"protocol_incomplete", "search_missing", "study_count", "pooling_not_justified"} <= codes
    with pytest.raises(ValueError, match="Freeze"):
        service.synthesize(record["id"])


@pytest.mark.parametrize("change, expected", [
    (lambda spec: spec["extractions"][0].update(scale="log ratio"), "incomparable_scale"),
    (lambda spec: spec["extractions"][0].update(units="um"), "incomparable_units"),
    (lambda spec: spec["extractions"][0].update(direction="opposite"), "incomparable_direction"),
    (lambda spec: spec["extractions"][0].update(quote="invented source quote"), "quote_mismatch"),
    (lambda spec: spec["extractions"][0]["verification"].update(status="extracted"), "source_not_checked"),
    (lambda spec: spec["studies"][1].update(independence_id="simulation-A"), "dependent_studies"),
    (lambda spec: spec["studies"][3].update(status="included"), "duplicate_report"),
    (lambda spec: spec["studies"][4].update(status="pending"), "selection_pending"),
    (lambda spec: spec["comparability"].update(pooling_justified=False), "pooling_not_justified"),
])
def test_unsafe_pooling_and_unverified_extraction_are_blocked(review, change, expected):
    _, service, record, spec = review
    changed = deepcopy(spec)
    change(changed)
    service.update(record["id"], record["revision"], changed)
    assert expected in {issue["code"] for issue in service.check(record["id"])["issues"]}
    with pytest.raises(ValueError, match="cannot freeze"):
        service.freeze(record["id"], DECISION)


def test_source_correction_reopens_extraction_and_invalidates_outputs(review):
    workspace, service, record, spec = review
    service.freeze(record["id"], DECISION)
    result = service.synthesize(record["id"])
    source = workspace.get_record(spec["extractions"][0]["source_id"])
    workspace.update_record(source["id"], expected_revision=source["revision"], content=source["content"] + "\nCorrection: uncertainty unresolved.")
    assert "stale_extraction" in {issue["code"] for issue in service.check(record["id"])["issues"]}
    with pytest.raises(RuntimeError):
        workspace.validate_current(result["figure"]["id"])
    with pytest.raises(RuntimeError):
        service.synthesize(record["id"])


def test_postfreeze_plan_edit_requires_new_freeze_and_preserves_history(review):
    workspace, service, record, spec = review
    frozen = service.freeze(record["id"], DECISION)
    result = service.synthesize(record["id"])
    updated_protocol = {**spec["protocol"], "model": "fixed"}
    updated = service.update(record["id"], frozen["revision"], {"protocol": updated_protocol})
    assert updated["metadata"]["state"] == "draft"
    assert updated["metadata"]["reopened_from_freeze"] == frozen["metadata"]["freeze_sha256"]
    with pytest.raises(ValueError, match="Freeze"):
        service.synthesize(record["id"])
    assert workspace.get_run(result["run"]["id"])["files"]
    with pytest.raises(RuntimeError):
        workspace.validate_current(result["figure"]["id"])


def test_agents_cannot_freeze_real_science_and_revision_checks_prevent_overwrite(review):
    _, service, record, _ = review
    updated = service.update(record["id"], record["revision"], {"synthetic": False})
    with pytest.raises(ValueError, match="agent cannot"):
        service.freeze(record["id"], DECISION)
    with pytest.raises(RuntimeError, match="changed"):
        service.freeze(record["id"], {**DECISION, "actor_type": "human", "kind": "scientific_approval"}, expected_revision=record["revision"])
    assert updated["metadata"]["state"] == "draft"
