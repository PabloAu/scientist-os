import json

import pytest

from scientist_os.host_state import HostState
from scientist_os.workspace import Workspace


def test_empty_project_correction_and_reopen(tmp_path):
    state = HostState(Workspace(tmp_path))
    assert state.context()["records"] == []
    project = state.start_project("Fictional assay", "Compare two protocols", scientist="Example owner",
                                  scope="Fictional training data only", host={"model": "example", "api_key": "secret"})
    correction = state.remember("correction", "Compare preparation days, not individual images",
                                attributed_to="Example owner", authority="project_status",
                                supersedes=project["id"])
    later = HostState(Workspace(tmp_path)).context()
    records = {record["id"]: record for record in later["records"]}
    assert records[project["id"]]["superseded_by"] == correction["id"]
    assert records[project["id"]]["metadata"]["host"]["api_key"] == "[REDACTED]"
    assert records[correction["id"]]["metadata"]["attributed_to"] == "Example owner"
    with pytest.raises(RuntimeError, match="already exists"):
        state.start_project("Other", "", scientist="Owner", scope="test")


def test_interrupt_resume_never_replays_uncertain_external_action(tmp_path):
    state = HostState(Workspace(tmp_path))
    task = state.task("Submit report", "Create an explicitly authorized report", steps=["export", "upload"])
    completed = state.begin_action(task["id"], key="export-1", tool="export", arguments={})
    assert completed["should_execute"]
    state.finish_action(completed["id"], result={"file": "report.docx"})
    external = state.begin_action(task["id"], key="upload-1", tool="upload", arguments={"file": "report.docx"},
                                  effect="external")
    # Simulate process death after external execution but before result persistence.
    state = HostState(Workspace(tmp_path))
    recovered = state.recover(task["id"])
    assert recovered["needs_reconciliation"] == [external["id"]]
    assert all(not a["should_execute"] for a in recovered["actions"])
    with pytest.raises(RuntimeError, match="resume"):
        state.begin_action(task["id"], key="another", tool="upload", arguments={})
    state.checkpoint(task["id"], status="running", summary="Inspect remote outcome")
    assert not state.begin_action(task["id"], key="upload-1", tool="upload", arguments={"file": "report.docx"},
                                   effect="external")["should_execute"]
    with pytest.raises(RuntimeError, match="Reconcile"):
        state.checkpoint(task["id"], status="completed", summary="done")
    state.reconcile_action(external["id"], outcome="completed", evidence="Remote ID matches the content digest",
                            attributed_to="host observation")
    state.checkpoint(task["id"], status="completed", summary="Outcome checked")
    assert state.recover(task["id"])["task"]["metadata"]["status"] == "completed"


def test_action_key_argument_conflict_and_stale_steering(tmp_path):
    state = HostState(Workspace(tmp_path))
    task = state.task("Analyze", "Calculate estimates")
    first = state.begin_action(task["id"], key="run-1", tool="execute", arguments={"dataset": "v1"})
    assert first["should_execute"]
    with pytest.raises(RuntimeError, match="different work"):
        state.begin_action(task["id"], key="run-1", tool="execute", arguments={"dataset": "v2"})
    state.checkpoint(task["id"], status="paused", summary="Scientist steers to another estimand")
    with pytest.raises(RuntimeError, match="changed"):
        state.checkpoint(task["id"], status="running", summary="Old host turn", expected_revision=1)


def test_actual_experiment_preserves_plan_and_missing_facts(tmp_path):
    state = HostState(Workspace(tmp_path))
    experiment = state.record_science("experiment", "Example assay", facts={
        "question": "Does the calibration change?", "independence_unit": "preparation_day",
        "controls": ["blank"], "temperature": 20,
    })
    assert "materials" in experiment["metadata"]["missing_facts"]
    with pytest.raises(ValueError, match="owner_statement"):
        state.reconcile_experiment(experiment["id"], actual={"temperature": 22}, attributed_to="scientist")
    actual = state.reconcile_experiment(experiment["id"], actual={
        "temperature": 22, "owner_statement": "The actual recorded temperature was 22 degrees C"
    }, attributed_to="Example owner")
    assert actual["metadata"]["scientific_state"] == "performed"
    assert actual["metadata"]["evidence_state"] == "registered"
    assert actual["metadata"]["planned"]["temperature"] == 20
    assert actual["metadata"]["deviations"]["temperature"] == {"planned": 20, "actual": 22}
    assert "independence_unit" in actual["metadata"]["unresolved_plan_fields"]


def test_scoped_corpus_progress_requires_decision_and_retains_other_scope(tmp_path):
    state = HostState(Workspace(tmp_path))
    source = state.workspace.create_record("source", "Paper", "Fictional evidence")
    scope = "claim:calibration"
    with pytest.raises(ValueError, match="skip"):
        state.advance_evidence(source["id"], state="verified", scope=scope,
                                checks={"original_checked": "p1", "authority_checked": "original study",
                                        "conflicts_checked": "no conflict in example"})
    progression = [
        ("classified", {"classification": "fictional primary study"}),
        ("extracted", {"extraction_method": "native text", "locators": ["p1"]}),
        ("mapped", {"claim_or_term": scope, "support_limit": "fictional illustration only"}),
        ("verified", {"original_checked": "p1", "authority_checked": "fictional primary study",
                      "conflicts_checked": "fixture counterpart compared"}),
    ]
    for stage, checks in progression:
        state.advance_evidence(source["id"], state=stage, scope=scope, checks=checks)
    with pytest.raises(ValueError, match="decision"):
        state.advance_evidence(source["id"], state="approved-for-use", scope=scope, checks={})
    wrong = state.remember("decision", "Approve this illustrative scope", attributed_to="Example owner",
                            authority="project_status", decision_status="recorded_human_decision", scope="other")
    with pytest.raises(ValueError, match="exact scope"):
        state.advance_evidence(source["id"], state="approved-for-use", scope=scope, checks={}, decision_id=wrong["id"])
    right = state.remember("decision", "Approve only the fictional calibration claim", attributed_to="Example owner",
                            authority="project_status", decision_status="recorded_human_decision", scope=scope,
                            source_ids=[source["id"]])
    record = state.advance_evidence(source["id"], state="approved-for-use", scope=scope, checks={}, decision_id=right["id"])
    assert record["metadata"]["corpus_scopes"][scope]["state"] == "approved-for-use"
    assert record["review_status"] == "unreviewed"
    assert state.workspace.get_record(right["id"])["metadata"]["identity_verified"] is False
    state.workspace.update_record(right["id"], expected_revision=right["revision"], content="Reconsider the scope")
    current = next(item for item in state.context()["records"] if item["id"] == source["id"])
    assert current["corpus_scope_freshness"][scope]["freshness"] == "stale"
    assert not current["corpus_scope_freshness"][scope]["permitted_for_use"]


@pytest.mark.parametrize("correction", ["content", "metadata", "upstream"])
def test_approval_cannot_survive_changed_science_or_reuse_old_decision(tmp_path, correction):
    """Attributed decisions here are fictional API fixtures, never actual human approvals."""
    state = HostState(Workspace(tmp_path))
    upstream = state.workspace.create_record("source", "Fictional original", "Positive effect")
    source = state.workspace.create_record("source", "Fictional extraction", "Positive effect",
                                           metadata={"units": "nm"}, links=[upstream["id"]])
    scope = "claim:fictional-direction"
    progression = [
        ("classified", {"classification": "fictional test material"}),
        ("extracted", {"extraction_method": "fixture text", "locators": ["fixture p1"]}),
        ("mapped", {"claim_or_term": scope, "support_limit": "no scientific claim"}),
        ("verified", {"original_checked": "fixture p1", "authority_checked": "fictional",
                      "conflicts_checked": "fixture comparison"}),
    ]

    def verify():
        for stage, checks in progression:
            state.advance_evidence(source["id"], state=stage, scope=scope, checks=checks)

    def decision():
        return state.remember("decision", "Fictional approval statement for API testing only",
            attributed_to="Fictional decision fixture (not a real reviewer)", authority="project_status",
            decision_status="recorded_human_decision", scope=scope, source_ids=[source["id"]])

    verify()
    old_decision = decision()
    approved = state.advance_evidence(source["id"], state="approved-for-use", scope=scope,
                                      checks={}, decision_id=old_decision["id"])
    assert state._scope_freshness(approved)[scope]["permitted_for_use"]
    # Changing only corpus bookkeeping must not invalidate its own approval decision.
    assert state.workspace.get_record(old_decision["id"])["revision"] == old_decision["revision"]
    if correction == "content":
        state.workspace.update_record(source["id"], expected_revision=approved["revision"],
                                       content="Negative effect")
    elif correction == "metadata":
        state.workspace.update_record(source["id"], expected_revision=approved["revision"],
                                       metadata={**approved["metadata"], "units": "um"})
    else:
        state.workspace.update_record(upstream["id"], expected_revision=upstream["revision"],
                                       content="Negative effect")
    current = next(item for item in state.context()["records"] if item["id"] == source["id"])
    assert not current["corpus_scope_freshness"][scope]["permitted_for_use"]
    with pytest.raises(ValueError, match="skip"):
        state.advance_evidence(source["id"], state="approved-for-use", scope=scope,
                                checks={}, decision_id=old_decision["id"])
    verify()
    with pytest.raises(ValueError, match="exact source evidence"):
        state.advance_evidence(source["id"], state="approved-for-use", scope=scope,
                                checks={}, decision_id=old_decision["id"])
    renewed = decision()
    approved = state.advance_evidence(source["id"], state="approved-for-use", scope=scope,
                                      checks={}, decision_id=renewed["id"])
    assert state._scope_freshness(approved)[scope]["permitted_for_use"]


@pytest.mark.parametrize("supersession", ["correction", "decision"])
def test_superseded_decision_cannot_keep_or_restore_corpus_approval(tmp_path, supersession):
    """Exercise fictional decision records without claiming actual human review."""
    state = HostState(Workspace(tmp_path))
    source = state.workspace.create_record("source", "Fictional paper", "Fixture evidence")
    scope = "claim:fixture-use"
    for stage, checks in [
        ("classified", {"classification": "fictional fixture"}),
        ("extracted", {"extraction_method": "fixture text", "locators": ["p1"]}),
        ("mapped", {"claim_or_term": scope, "support_limit": "test only"}),
        ("verified", {"original_checked": "fixture p1", "authority_checked": "fictional",
                      "conflicts_checked": "test counterpart"}),
    ]:
        state.advance_evidence(source["id"], state=stage, scope=scope, checks=checks)

    def decision(**kwargs):
        return state.remember("decision", "Fictional API approval fixture, not human review",
            attributed_to="Fictional decision fixture", authority="project_status",
            decision_status="recorded_human_decision", scope=scope,
            source_ids=[source["id"]], **kwargs)

    previous = decision()
    approved = state.advance_evidence(source["id"], state="approved-for-use", scope=scope,
                                      checks={}, decision_id=previous["id"])
    if supersession == "correction":
        correction = state.remember("correction", "Withdraw the previous fictional approval",
            attributed_to="Fictional decision fixture", authority="project_status",
            supersedes=previous["id"])
        renewed = None
    else:
        renewed = decision(supersedes=previous["id"])

    # This uses the normal correction path: neither evidence nor the prior decision was edited.
    state = HostState(Workspace(tmp_path))
    assert state.workspace.get_record(previous["id"])["revision"] == previous["revision"]
    assert state.workspace.get_record(source["id"])["revision"] == approved["revision"]
    records = {item["id"]: item for item in state.context()["records"]}
    assert records[previous["id"]]["superseded_by"] == (
        correction["id"] if supersession == "correction" else renewed["id"])
    assert not records[source["id"]]["corpus_scope_freshness"][scope]["permitted_for_use"]
    with pytest.raises(ValueError, match="superseded"):
        state.advance_evidence(source["id"], state="approved-for-use", scope=scope,
                                checks={}, decision_id=previous["id"])
    renewed = renewed or decision(supersedes=correction["id"])
    approved = state.advance_evidence(source["id"], state="approved-for-use", scope=scope,
                                      checks={}, decision_id=renewed["id"])
    assert state._scope_freshness(approved)[scope]["permitted_for_use"]


def test_context_routes_full_metadata_freshness_and_exports(tmp_path):
    state = HostState(Workspace(tmp_path))
    dataset = state.workspace.create_record("dataset", "Input", "value\n1", metadata={
        "units": "nm", "independence_unit": "day", "nested_units": ["cell", "frame"], "password": "do not disclose"})
    result = state.workspace.create_record("analysis", "Estimate", "1 nm", links=[dataset["id"]],
                                           metadata={"input_revisions": {dataset["id"]: 1}})
    state.workspace.update_record(dataset["id"], expected_revision=1, content="value\n2")
    current = state.context(authority="raw_metadata")["records"][0]
    assert current["metadata"]["independence_unit"] == "day"
    assert current["metadata"]["password"] == "[REDACTED]"
    assert current["untrusted_data"]
    assert state.context(authority="analysis")["records"][0]["freshness"] == "stale"
    assert result["id"] in json.dumps(state.context())
    exported = state.export_context()
    assert exported["record_count"] == 2
    assert json.loads((tmp_path / "host-context" / "CONTEXT.json").read_text(encoding="utf-8"))["records"]
    assert not state.workspace.audit() or all(a["code"] != "event_chain_invalid" for a in state.workspace.audit())


def test_export_rejects_link_destination(tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    outside.mkdir()
    state = HostState(Workspace(workspace))
    try:
        (workspace / "host-context").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Host does not grant symlink creation")
    with pytest.raises(ValueError, match="inside"):
        state.export_context()
