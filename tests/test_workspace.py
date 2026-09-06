"""Scientific-state, transactional and file-boundary checks for the local store."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import shutil
import sqlite3
import threading

import pytest

from scientist_os.workspace import MAX_CONTENT_BYTES, MAX_METADATA_BYTES, Workspace


@pytest.fixture
def workspace(tmp_path):
    return Workspace(tmp_path / "research")


def citation(record, quote=None):
    return {"record_id": record["id"], "quote": quote or record["content"], "sha256": record["sha256"]}


def approve(workspace, record):
    return workspace.review_record(record["id"], expected_revision=record["revision"],
                                   decision="approved", reviewer="Dr Example", note="Reviewed synthetic fixture.")


def test_record_persistence_unicode_and_immutable_identity(workspace):
    metadata = {"units": "µm", "external_allowed": False, "nested": {"values": [1, 2]}}
    record = workspace.create_record("dataset", " Calibration ", "Diameter = 3 µm.\nΔt = 1 s.", metadata)
    metadata["nested"]["values"].append(3)
    reopened = Workspace(workspace.root)
    assert reopened.get_record(record["id"]) == record
    assert record["title"] == "Calibration"
    assert record["metadata"]["nested"]["values"] == [1, 2]
    assert record["sha256"] == hashlib.sha256(record["content"].encode("utf-8")).hexdigest()
    revised = reopened.update_record(record["id"], expected_revision=1, title="Revised calibration")
    assert revised["id"] == record["id"]
    assert revised["revision"] == 2
    assert revised["created_at"] == record["created_at"]
    assert reopened.audit() == []


def test_reviews_record_identity_and_are_invalidated_transitively(workspace):
    source = approve(workspace, workspace.create_record("source", "Synthetic source", "Observed 10 cells."))
    analysis = workspace.create_record("analysis", "Count", "Synthetic count is ten.",
                                      {"citations": [citation(source)], "input_revisions": {source["id"]: source["revision"]}},
                                      [source["id"]])
    analysis = approve(workspace, analysis)
    manuscript = approve(workspace, workspace.create_record("manuscript", "Draft", "Ten cells.", links=[analysis["id"]]))
    workspace.update_record(source["id"], expected_revision=source["revision"], content="Observed 12 cells.")
    invalid_analysis = workspace.get_record(analysis["id"])
    invalid_draft = workspace.get_record(manuscript["id"])
    assert invalid_analysis["review_status"] == invalid_draft["review_status"] == "unreviewed"
    assert invalid_analysis["revision"] == analysis["revision"] + 1
    assert invalid_draft["revision"] == manuscript["revision"] + 1
    codes = {finding["code"] for finding in workspace.audit()}
    assert {"citation_hash_mismatch", "citation_quote_mismatch", "stale_input_revision"} <= codes
    with pytest.raises(RuntimeError, match="Citation source hash changed"):
        approve(workspace, invalid_analysis)
    events = workspace.events()
    human_reviews = [event for event in events if event["action"] == "record_reviewed"]
    assert human_reviews[-1]["data"]["reviewer"] == "Dr Example"
    assert len([event for event in events if event["action"] == "dependency_invalidated"]) == 2


def test_citation_and_input_dependencies_invalidate_without_explicit_links(workspace):
    source = workspace.create_record("source", "Source", "Exact quote.")
    cited = approve(workspace, workspace.create_record("claim", "Claim", metadata={"citations": [citation(source)]}))
    derived = approve(workspace, workspace.create_record("analysis", "Derived", metadata={"input_revisions": {source["id"]: 1}}))
    workspace.update_record(source["id"], expected_revision=1, metadata={"units": "nm"})
    assert workspace.get_record(cited["id"])["review_status"] == "unreviewed"
    assert workspace.get_record(derived["id"])["review_status"] == "unreviewed"
    assert any(finding["code"] == "stale_input_revision" for finding in workspace.audit())


def test_reviewing_an_input_invalidates_older_revision_bound_results(workspace):
    source = workspace.create_record("dataset", "Synthetic input", "value\n1\n")
    analysis = approve(workspace, workspace.create_record("analysis", "Result", metadata={"input_revisions": {source["id"]: 1}}))
    approve(workspace, source)
    assert workspace.get_record(analysis["id"])["review_status"] == "unreviewed"
    assert any(finding["code"] == "stale_input_revision" for finding in workspace.audit())


def test_stale_ancestor_cannot_be_reused_to_create_or_approve_a_fresh_claim(workspace):
    source = workspace.create_record("dataset", "Input", "Old data")
    analysis = workspace.create_record("analysis", "Analysis", "The mean is ten.",
                                       metadata={"input_revisions": {source["id"]: 1}})
    claim = workspace.create_record("claim", "Claim", metadata={"citations": [citation(analysis)]})
    workspace.update_record(source["id"], expected_revision=1, content="Corrected data")
    stale_analysis = workspace.get_record(analysis["id"])
    stale_claim = workspace.get_record(claim["id"])
    # A current direct revision and unchanged quotation do not repair the
    # stale dataset revision underneath the cited analysis.
    before = workspace.events()
    with pytest.raises(RuntimeError, match="Input revision is stale"):
        workspace.create_record("claim", "New claim", metadata={
            "citations": [citation(stale_analysis)],
            "input_revisions": {analysis["id"]: stale_analysis["revision"]},
        })
    with pytest.raises(RuntimeError, match="Input revision is stale"):
        approve(workspace, stale_claim)
    with pytest.raises(RuntimeError, match="Input revision is stale"):
        workspace.update_record(claim["id"], expected_revision=stale_claim["revision"], title="Still stale")
    assert workspace.events() == before
    rejected = workspace.review_record(claim["id"], expected_revision=stale_claim["revision"],
                                       decision="rejected", reviewer="Dr Example", note="Upstream calculation is stale.")
    assert rejected["review_status"] == "rejected"


def test_validate_current_checks_ancestor_citations_without_returning_ancestor_text(workspace):
    source = workspace.create_record("source", "Private ancestor", "Original evidence")
    intermediate = workspace.create_record("claim", "Intermediate", "A derived assertion.",
                                           metadata={"citations": [citation(source)]})
    selected = workspace.create_record("note", "Selected record", "Selected content only", links=[intermediate["id"]])
    checked = workspace.validate_current(selected["id"])
    assert checked == selected
    assert "Original evidence" not in json.dumps(checked)
    assert checked["review_status"] == "unreviewed"  # Approval is not assumed or required.
    workspace.update_record(source["id"], expected_revision=1, content="Corrected evidence")
    with pytest.raises(RuntimeError, match="Citation source hash changed"):
        workspace.validate_current(selected["id"])
    assert workspace.get_record(selected["id"])["content"] == selected["content"]


def test_reconverging_valid_evidence_is_not_mistaken_for_a_cycle(workspace):
    source = workspace.create_record("source", "Shared original", "Evidence")
    left = workspace.create_record("note", "Left", links=[source["id"]])
    right = workspace.create_record("note", "Right", links=[source["id"], left["id"]])
    merged = workspace.create_record("claim", "Merged", links=[left["id"], right["id"]])
    assert workspace.validate_current(merged["id"]) == merged
    assert approve(workspace, merged)["review_status"] == "approved"


def test_rejected_stale_evidence_can_be_recorded_and_then_repaired(workspace):
    source = workspace.create_record("source", "Source", "Old evidence.")
    claim = workspace.create_record("claim", "Claim", metadata={"citations": [citation(source)]})
    source = workspace.update_record(source["id"], expected_revision=1, content="Corrected evidence.")
    claim = workspace.get_record(claim["id"])
    rejected = workspace.review_record(claim["id"], expected_revision=claim["revision"], decision="rejected",
                                       reviewer="Dr Example", note="Evidence corrected.")
    assert rejected["review_status"] == "rejected"
    corrected = workspace.update_record(claim["id"], expected_revision=rejected["revision"],
                                         metadata={"citations": [citation(source)]})
    assert approve(workspace, corrected)["review_status"] == "approved"
    assert workspace.audit() == []


@pytest.mark.parametrize("bad_id", ["../../outside", "source_../../secret", "C:\\private\\key", "' OR 1=1--", "", None, 1, "source_" + "a" * 33])
def test_untrusted_identifiers_never_become_paths_or_sql(workspace, bad_id):
    with pytest.raises(ValueError):
        workspace.get_record(bad_id)
    with pytest.raises(ValueError):
        workspace.update_record(bad_id, expected_revision=1, content="No write")
    with pytest.raises(ValueError):
        workspace.search("value", record_ids=[bad_id])
    with pytest.raises(ValueError):
        workspace.get_run(bad_id)
    assert workspace.events() == []


def test_missing_valid_identifiers_are_distinct_from_invalid_identifiers(workspace):
    with pytest.raises(KeyError):
        workspace.get_record("source_" + "a" * 32)
    with pytest.raises(KeyError):
        workspace.get_run("run_" + "a" * 32)
    with pytest.raises(ValueError, match="does not exist"):
        workspace.create_record("claim", "Dangling", links=["source_" + "a" * 32])
    assert workspace.list_records() == workspace.events() == []


@pytest.mark.parametrize("kwargs", [
    {"kind": "unknown"}, {"title": "  "}, {"title": "x" * 1001},
    {"content": "x" * (MAX_CONTENT_BYTES + 1)}, {"content": "bad\x00text"},
    {"metadata": {"number": float("nan")}}, {"metadata": {"number": float("inf")}},
    {"metadata": {"number": 1 << 300}}, {"metadata": {1: "non-string key"}},
    {"metadata": {"external_allowed": "true"}}, {"metadata": {"units": {1, 2}}},
    {"metadata": {"text": "x" * MAX_METADATA_BYTES}}, {"metadata": []},
    {"links": "source_" + "a" * 32}, {"content": "bad\ud800unicode"},
])
def test_invalid_record_input_has_no_partial_mutation(workspace, kwargs):
    arguments = {"kind": "note", "title": "Good", **kwargs}
    with pytest.raises(ValueError):
        workspace.create_record(**arguments)
    assert workspace.list_records() == workspace.events() == []


def test_json_cycles_depth_and_duplicate_links_rejected(workspace):
    cyclic = {}
    cyclic["cycle"] = cyclic
    with pytest.raises(ValueError, match="cycle"):
        workspace.create_record("note", "Cycle", metadata=cyclic)
    nested = {}
    for _ in range(22):
        nested = {"nested": nested}
    with pytest.raises(ValueError, match="nested"):
        workspace.create_record("note", "Deep", metadata=nested)
    source = workspace.create_record("source", "Source")
    with pytest.raises(ValueError, match="duplicates"):
        workspace.create_record("note", "Duplicate", links=[source["id"], source["id"]])


def test_self_reference_is_rejected_and_transaction_is_unchanged(workspace):
    record = workspace.create_record("note", "Note")
    before = workspace.events()
    with pytest.raises(ValueError, match="itself"):
        workspace.update_record(record["id"], expected_revision=1, links=[record["id"]])
    assert workspace.get_record(record["id"]) == record
    assert workspace.events() == before


def test_transitive_cycle_is_rejected_without_invalidating_existing_reviews(workspace):
    original = workspace.create_record("note", "Original")
    middle = workspace.create_record("analysis", "Middle", links=[original["id"]])
    downstream = approve(workspace, workspace.create_record("claim", "Downstream", links=[middle["id"]]))
    before = workspace.events()
    with pytest.raises(ValueError, match="Circular"):
        workspace.update_record(original["id"], expected_revision=1, links=[downstream["id"]])
    assert workspace.events() == before
    assert workspace.get_record(downstream["id"])["review_status"] == "approved"


def test_citation_validation_requires_exact_quote_current_hash_and_valid_shape(workspace):
    source = workspace.create_record("source", "Source", "No causal conclusion was established.")
    before = workspace.events()
    bad_hash = {**citation(source), "sha256": "0" * 64}
    with pytest.raises(RuntimeError, match="hash"):
        workspace.create_record("claim", "Wrong hash", metadata={"citations": [bad_hash]})
    with pytest.raises(ValueError, match="exact"):
        workspace.create_record("claim", "Fabricated", metadata={"citations": [citation(source, "A causal conclusion was established.")]})
    with pytest.raises(ValueError, match="exactly"):
        workspace.create_record("claim", "Malformed", metadata={"citations": [{"record_id": source["id"]}]})
    with pytest.raises(RuntimeError, match="stale"):
        workspace.create_record("analysis", "Stale", metadata={"input_revisions": {source["id"]: 2}})
    assert workspace.events() == before


def test_create_rollback_when_audit_event_cannot_be_written(workspace, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("Simulated event write failure")

    monkeypatch.setattr(workspace, "_append_event", fail)
    with pytest.raises(RuntimeError, match="Simulated"):
        workspace.create_record("source", "Cannot partially persist", "Important evidence")
    assert workspace.list_records() == workspace.events() == []


def test_source_and_all_dependents_roll_back_on_midway_failure(workspace, monkeypatch):
    source = workspace.create_record("source", "Source", "Original")
    dependent = approve(workspace, workspace.create_record("analysis", "Dependent", links=[source["id"]]))
    records_before = workspace.list_records()
    events_before = workspace.events()
    original_append = workspace._append_event

    def fail_invalidation(connection, action, data, record_id=None):
        if action == "dependency_invalidated":
            raise RuntimeError("Simulated dependent event failure")
        return original_append(connection, action, data, record_id)

    monkeypatch.setattr(workspace, "_append_event", fail_invalidation)
    with pytest.raises(RuntimeError, match="Simulated"):
        workspace.update_record(source["id"], expected_revision=1, content="Changed")
    assert workspace.list_records() == records_before
    assert workspace.events() == events_before
    assert workspace.get_record(dependent["id"])["review_status"] == "approved"


def test_multi_record_transaction_commits_records_review_and_events_together(workspace):
    with workspace.transaction() as transaction:
        assert transaction is workspace
        source = workspace.create_record("dataset", "Input", "value\n1\n")
        analysis = workspace.create_record("analysis", "Result", metadata={"input_revisions": {source["id"]: 1}})
        reviewed = approve(workspace, analysis)
        figure = workspace.create_record("output", "Figure", links=[analysis["id"]],
                                         metadata={"input_revisions": {analysis["id"]: reviewed["revision"]}})
        assert workspace.get_record(figure["id"]) == figure
    assert len(workspace.list_records()) == 3
    assert len(workspace.events()) == 4
    assert workspace.audit() == []


def test_late_multi_record_failure_rolls_back_all_rows_and_events(workspace):
    with pytest.raises(ValueError, match="reviewer"):
        with workspace.transaction():
            record = workspace.create_record("decision", "Stage check", "Check result")
            workspace.review_record(record["id"], expected_revision=1, decision="approved", reviewer=" ")
    assert workspace.list_records() == workspace.events() == []


def test_nested_operation_failure_cannot_be_caught_to_commit_partial_state(workspace):
    with pytest.raises(RuntimeError, match="nested operation failed"):
        with workspace.transaction():
            source = workspace.create_record("source", "Source", "Evidence")
            try:
                with workspace.transaction():
                    workspace.create_record("note", "Temporary")
                    workspace.update_record(source["id"], expected_revision=999, content="Stale update")
            except RuntimeError:
                pass
    assert workspace.list_records() == workspace.events() == []
    assert workspace.create_record("note", "New transaction works")["revision"] == 1


def test_caught_input_validation_still_aborts_an_explicit_transaction(workspace):
    with pytest.raises(RuntimeError, match="nested operation failed"):
        with workspace.transaction():
            workspace.create_record("note", "Must be rolled back")
            try:
                workspace.create_record("note", "   ")
            except ValueError:
                pass
    assert workspace.list_records() == workspace.events() == []


def test_explicit_transaction_does_not_expose_uncommitted_rows_and_locks_writers(workspace):
    source = workspace.create_record("source", "Source", "Old evidence")
    independent = Workspace(workspace.root)
    with workspace.transaction():
        corrected = workspace.update_record(source["id"], expected_revision=1, content="Corrected evidence")
        dependent = workspace.create_record("claim", "Dependent", metadata={"citations": [citation(corrected)]})
        assert independent.get_record(source["id"])["content"] == "Old evidence"
        assert len(independent.list_records()) == 1
        with sqlite3.connect(workspace.db_path, timeout=0) as other_writer:
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                other_writer.execute("BEGIN IMMEDIATE")
    assert independent.get_record(source["id"])["content"] == "Corrected evidence"
    assert independent.get_record(dependent["id"]) == dependent
    assert independent.audit() == []


def test_transaction_connection_is_not_shared_with_other_threads(workspace):
    with ThreadPoolExecutor(max_workers=1) as executor:
        with workspace.transaction():
            created = workspace.create_record("note", "Uncommitted")
            # Reusing the instance from another thread must get its own reader,
            # which cannot see this thread's uncommitted record.
            assert executor.submit(workspace.list_records).result(timeout=5) == []
        assert executor.submit(workspace.get_record, created["id"]).result(timeout=5) == created


def test_readonly_connection_cannot_be_reused_as_writer(workspace):
    with pytest.raises(RuntimeError, match="read-only"):
        with workspace._connection():
            with workspace.transaction():
                workspace.create_record("note", "Must not write")
    assert workspace.list_records() == workspace.events() == []


def test_optimistic_revision_conflict_across_connections(workspace):
    record = workspace.create_record("note", "Concurrent")
    barrier = threading.Barrier(2)

    def update(content):
        separate = Workspace(workspace.root)
        barrier.wait(timeout=10)
        try:
            return separate.update_record(record["id"], expected_revision=1, content=content)
        except RuntimeError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(update, ["First writer", "Second writer"]))
    assert len([result for result in results if isinstance(result, dict)]) == 1
    assert len([result for result in results if isinstance(result, str) and "Stale revision" in result]) == 1
    assert workspace.get_record(record["id"])["revision"] == 2
    assert len(workspace.events()) == 2
    assert workspace.audit() == []


@pytest.mark.parametrize("revision", [True, False, 0, -1, 1.0, "1", 1 << 64])
def test_revision_is_a_strict_positive_integer(workspace, revision):
    record = workspace.create_record("note", "Revision")
    with pytest.raises(ValueError):
        workspace.update_record(record["id"], expected_revision=revision, content="Changed")
    assert workspace.get_record(record["id"]) == record


def test_review_requires_human_attribution_and_current_version(workspace):
    record = workspace.create_record("note", "Review")
    with pytest.raises(ValueError):
        workspace.review_record(record["id"], expected_revision=1, decision="approved", reviewer=" ")
    with pytest.raises(ValueError):
        workspace.review_record(record["id"], expected_revision=1, decision="validated", reviewer="Dr Example")
    approved = approve(workspace, record)
    with pytest.raises(RuntimeError, match="Stale"):
        approve(workspace, record)
    changed = workspace.update_record(record["id"], expected_revision=approved["revision"], title="Correction")
    assert changed["review_status"] == "unreviewed"


def test_scoped_search_returns_only_exact_selected_excerpts(workspace):
    chosen = workspace.create_record("source", "Selected", "ß " + "α" * 900 + " observed signal in µm.")
    workspace.create_record("source", "Private signal", "Unselected private signal, signal, signal")
    result = workspace.search("signal", record_ids=[chosen["id"]])
    assert len(result) == 1
    assert result[0]["record_id"] == chosen["id"]
    assert result[0]["quote"] in chosen["content"]
    assert "signal" in result[0]["quote"]
    assert result[0]["sha256"] == chosen["sha256"]
    assert workspace.search("signal", record_ids=[]) == []
    with pytest.raises(ValueError):
        workspace.search(" ")
    with pytest.raises(ValueError):
        workspace.search("%")
    with pytest.raises(ValueError):
        workspace.search("signal", limit=True)


def test_runs_are_immutable_redacted_and_preserve_trace(workspace):
    raw = {"status": "needs_review", "question": "Explain synthetic data", "provider": "demo",
           "config": {"api_key": "very-private", "Authorization": "Bearer abcdefghi1234", "model": "demo", "X-API-Key": "other-private"},
           "trace": [{"tool": "search", "result": "Observed value"}],
           "diagnostic": "Bearer long_secret_token_123"}
    run = workspace.save_run(raw)
    assert "id" not in raw
    assert run["config"]["api_key"] == run["config"]["Authorization"] == "[REDACTED]"
    assert run["config"]["X-API-Key"] == "[REDACTED]"
    assert "long_secret_token_123" not in run["diagnostic"]
    assert workspace.get_run(run["id"])["trace"] == raw["trace"]
    assert workspace.list_runs() == [run]
    before = workspace.events()
    with pytest.raises(RuntimeError):
        workspace.save_run(run)
    assert workspace.events() == before
    assert "very-private" not in json.dumps(workspace.export_bundle())
    assert workspace.audit() == []


def test_run_rejects_malformed_or_path_like_id_and_rolls_back_audit_failure(workspace, monkeypatch):
    with pytest.raises(ValueError):
        workspace.save_run({"id": "../../private"})
    with pytest.raises(ValueError):
        workspace.save_run({"value": float("nan")})
    with pytest.raises(ValueError):
        workspace.save_run({"trace": "x" * (4 * 1024 * 1024 + 1)})

    def fail(*args, **kwargs):
        raise RuntimeError("Simulated event failure")

    monkeypatch.setattr(workspace, "_append_event", fail)
    with pytest.raises(RuntimeError):
        workspace.save_run({"status": "needs_review"})
    assert workspace.list_runs() == workspace.events() == []


@pytest.mark.parametrize("secret", [
    "Bearer abcdefghijklmnopqrstuvwxyz", "sk-abcdefghijklmnopqrstuvwx",
    "ghp_abcdefghijklmnopqrstuvwx", "hf_abcdefghijklmnopqrstuvwx",
])
def test_run_redaction_drops_altered_exact_quotes_and_marks_unsupported(workspace, secret):
    source = workspace.create_record("source", "Synthetic token fixture", f"A credential-shaped value: {secret}")
    original_citation = citation(source)
    raw = {"status": "needs_review", "answer": "Proposed interpretation.", "grounding": "verified_quotes",
           "citations": [original_citation], "warnings": ["Human review required."]}
    saved = workspace.save_run(raw)
    assert saved["citations"] == []
    assert saved["grounding"] == "unsupported"
    assert saved["status"] == "needs_review"
    assert saved["answer"].startswith("Unsupported proposal")
    assert saved["redaction_applied"] is True
    assert saved["citation_redaction"]["removed"] == 1
    assert secret not in json.dumps(saved)
    assert raw["citations"] == [original_citation]
    assert raw["grounding"] == "verified_quotes"
    assert workspace.get_run(saved["id"]) == saved


def test_run_redaction_retains_unchanged_exact_quotes(workspace):
    safe_source = workspace.create_record("source", "Safe source", "Three independent days were recorded.")
    token_source = workspace.create_record("source", "Token fixture", "Bearer abcdefghijklmnopqrstuvwxyz")
    saved = workspace.save_run({"status": "needs_review", "answer": "Review these observations.",
                                "grounding": "verified_quotes", "citations": [citation(safe_source), citation(token_source)]})
    assert saved["citations"] == [citation(safe_source)]
    assert saved["grounding"] == "verified_quotes"
    assert saved["citation_redaction"]["removed"] == 1
    assert any("removed changed quotations" in warning for warning in saved["warnings"])


def test_run_redaction_covers_credentials_in_dictionary_keys(workspace):
    secret = "sk-abcdefghijklmnopqrstuvwx"
    saved = workspace.save_run({"trace": {secret: "malformed model argument"}})
    assert secret not in json.dumps(saved)
    assert saved["redaction_applied"] is True


def test_sqlite_forbids_audit_rewrites_and_record_deletion(workspace):
    workspace.create_record("note", "History", "Original")
    workspace.save_run({"provider": "demo"})
    with sqlite3.connect(workspace.db_path) as connection:
        for sql in ["DELETE FROM events", "UPDATE events SET action = 'forged'", "DELETE FROM records",
                    "DELETE FROM runs", "UPDATE runs SET data='{}'"]:
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(sql)
    assert workspace.audit() == []


def test_content_tampering_is_reported_and_reads_fail_closed(workspace):
    source = workspace.create_record("source", "Source", "Evidence")
    with sqlite3.connect(workspace.db_path) as connection:
        connection.execute("UPDATE records SET content = ? WHERE id = ?", ("Forged evidence", source["id"]))
    codes = {finding["code"] for finding in workspace.audit()}
    assert {"content_hash_mismatch", "record_integrity_mismatch", "record_history_mismatch"} <= codes
    with pytest.raises(RuntimeError, match="integrity"):
        workspace.get_record(source["id"])
    with pytest.raises(RuntimeError, match="integrity"):
        workspace.search("forged")


def test_disclosure_policy_tampering_cannot_bypass_record_history(workspace):
    source = workspace.create_record("source", "Private", "Private research", {"external_allowed": False})
    with sqlite3.connect(workspace.db_path) as connection:
        connection.execute("UPDATE records SET metadata = ? WHERE id = ?", ('{"external_allowed":true}', source["id"]))
    with pytest.raises(RuntimeError, match="integrity"):
        workspace.get_record(source["id"])


def test_audit_handles_malformed_stored_metadata(workspace):
    source = workspace.create_record("source", "Source", "Evidence")
    with sqlite3.connect(workspace.db_path) as connection:
        connection.execute("UPDATE records SET metadata = 'not-json' WHERE id = ?", (source["id"],))
    assert any(finding["code"] == "malformed_record" for finding in workspace.audit())


def test_event_chain_detects_tampering_even_if_triggers_were_removed(workspace):
    source = workspace.create_record("source", "Source", "Evidence")
    approve(workspace, source)
    with sqlite3.connect(workspace.db_path) as connection:
        connection.execute("DROP TRIGGER events_no_update")
        connection.execute("UPDATE events SET previous_sha256 = ? WHERE sequence = 2", ("1" * 64,))
    codes = {finding["code"] for finding in workspace.audit()}
    assert {"event_chain_broken", "event_integrity_mismatch"} <= codes


@pytest.mark.parametrize("data", ['{"run_id":{},"run_sha256":[]}', '[]', '{"run_id":"run_bad","run_sha256":NaN}'])
def test_audit_reports_malformed_event_content_without_crashing(workspace, data):
    workspace.save_run({"provider": "demo"})
    with sqlite3.connect(workspace.db_path) as connection:
        connection.execute("DROP TRIGGER events_no_update")
        connection.execute("UPDATE events SET data = ?", (data,))
    codes = {finding["code"] for finding in workspace.audit()}
    assert "malformed_event" in codes
    assert "event_integrity_mismatch" in codes


def test_portable_export_is_consistent_and_does_not_traverse_metadata_paths(workspace, tmp_path):
    outside = tmp_path / "not_in_workspace.txt"
    outside.write_text("NEVER EXPORT THIS FILE", encoding="utf-8")
    workspace.create_record("dataset", "Registered path", "value\n1\n", metadata={"path": str(outside), "relative_path": "../../other"})
    workspace.save_run({"status": "needs_review", "provider": "demo"})
    bundle = workspace.export_bundle()
    serialized = json.dumps(bundle, ensure_ascii=False)
    assert "NEVER EXPORT THIS FILE" not in serialized
    assert bundle["schema_version"] == 1
    assert bundle["integrity_manifest"]["findings"] == []
    claimed_digest = bundle["integrity_manifest"].pop("bundle_sha256")
    canonical = json.dumps(bundle, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == claimed_digest
    copy_root = tmp_path / "moved-workspace"
    shutil.copytree(workspace.root, copy_root)
    moved = Workspace(copy_root)
    assert moved.list_records() == workspace.list_records()
    assert moved.list_runs() == workspace.list_runs()
    assert moved.events() == workspace.events()
    assert moved.audit() == []


def test_unknown_schema_version_is_not_silently_migrated(workspace):
    with sqlite3.connect(workspace.db_path) as connection:
        connection.execute("PRAGMA user_version = 999")
    with pytest.raises(RuntimeError, match="Unsupported workspace schema"):
        Workspace(workspace.root)
