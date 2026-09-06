"""Authoring races, exact selections, reference integrity and scoped dialogue."""

from copy import deepcopy
import json

import pytest

from scientist_os.providers import ScriptedProvider, tool_message
from scientist_os.studio import (
    apply_passage, create_discussion, create_manuscript, create_reference, discuss,
    propose_passage, update_manuscript, update_reference,
)
from scientist_os.workspace import Workspace


@pytest.fixture
def study(tmp_path):
    workspace = Workspace(tmp_path / "study")
    source = workspace.create_record("source", "Fictional microscopy observation", "Three independent preparations were imaged.")
    manuscript = create_manuscript(workspace, title="Fictional draft", sections=[
        {"title": "Results", "text": "A 🧫 measured β signal. PRIVATE_UNSELECTED_SECTION_CONTENT"},
        {"title": "Private ideas", "text": "PRIVATE_OTHER_SECTION_CONTENT"},
    ])
    return workspace, source, manuscript


def response(source, answer="The signal was measured."):
    return tool_message("finish", {"answer": answer, "citations": [{
        "record_id": source["id"], "sha256": source["sha256"], "quote": source["content"],
    }]})


def proposal(study, provider=None, **overrides):
    workspace, source, manuscript = study
    values = dict(expected_revision=manuscript["revision"], section_id=manuscript["metadata"]["sections"][0]["id"],
                  start=2, end=4, selected_text="🧫", instruction="Refine this wording.", source_ids=[source["id"]])
    values.update(overrides)
    return propose_passage(workspace, provider or ScriptedProvider([response(source)]), manuscript["id"], **values)


def test_manuscript_defaults_and_stable_section_reordering(tmp_path):
    workspace = Workspace(tmp_path)
    manuscript = create_manuscript(workspace, title="Study")
    sections = manuscript["metadata"]["sections"]
    assert [s["title"] for s in sections] == ["Abstract", "Introduction", "Methods", "Results", "Discussion", "Supplementary material"]
    assert sections[-1]["supplementary"] is True
    revised = update_manuscript(workspace, manuscript["id"], expected_revision=1, sections=list(reversed(sections)))
    assert revised["metadata"]["sections"][0]["id"] == sections[-1]["id"]
    assert revised["revision"] == 2 and revised["review_status"] == "unreviewed"
    assert workspace.audit() == []


def test_selection_discloses_only_exact_passage_and_explicit_evidence(study):
    workspace, source, manuscript = study
    provider = ScriptedProvider([response(source)])
    result = proposal(study, provider)
    calls = json.dumps(provider.calls, ensure_ascii=False)
    assert "🧫" in calls
    assert "PRIVATE_UNSELECTED_SECTION_CONTENT" not in calls
    assert "PRIVATE_OTHER_SECTION_CONTENT" not in calls
    assert result["proposal"]["review_status"] == "unreviewed"
    assert result["proposal"]["metadata"]["selection"]["offset_encoding"] == "utf-16"
    assert workspace.get_record(manuscript["id"]) == manuscript
    assert result["run"]["status"] == "needs_review"


@pytest.mark.parametrize("start,end,text,exception", [
    (2, 3, "", ValueError), (3, 4, "", ValueError), (2, 4, "wrong", RuntimeError),
    (-1, 0, "", ValueError), (4, 2, "", ValueError), (False, 4, "", ValueError),
    (0, 500, "", ValueError), ("2", 4, "", ValueError),
])
def test_invalid_or_half_surrogate_offsets_make_no_model_request(study, start, end, text, exception):
    provider = ScriptedProvider([])
    with pytest.raises(exception):
        proposal(study, provider, start=start, end=end, selected_text=text)
    assert provider.calls == []
    assert study[0].list_runs() == []


def test_apply_is_named_atomic_human_edit_with_immutable_history(study):
    workspace, source, manuscript = study
    result = proposal(study)
    with pytest.raises(ValueError, match="reviewer"):
        apply_passage(workspace, manuscript["id"], result["proposal"]["id"], expected_revision=1, reviewer="  ")
    before = workspace.export_bundle()
    applied = apply_passage(workspace, manuscript["id"], result["proposal"]["id"], expected_revision=1,
                            reviewer="Synthetic UI tester", replacement="fluorescent cells", note="Fictional workflow test")
    manuscript_after = applied["manuscript"]
    assert manuscript_after["metadata"]["sections"][0]["text"].startswith("A fluorescent cells measured β signal.")
    assert manuscript_after["review_status"] == "unreviewed"
    assert applied["proposal"]["review_status"] == "approved"
    assert applied["proposal"]["metadata"]["state"] == "applied"
    assert applied["proposal"]["content"] == result["proposal"]["content"]
    assert manuscript_after["metadata"]["accepted_evidence_revisions"] == {source["id"]: 1}
    assert manuscript_after["metadata"]["applied_proposals"][0]["human_edited"] is True
    assert workspace.export_bundle()["events"][:len(before["events"])] == before["events"]
    assert any(e["action"] == "record_reviewed" and e["data"].get("reviewer") == "Synthetic UI tester" for e in workspace.events())
    reopened = Workspace(workspace.root)
    assert reopened.get_record(manuscript["id"]) == manuscript_after
    assert reopened.audit() == []


def test_empty_selection_can_insert_without_replacing_neighboring_unicode(study):
    workspace, _, manuscript = study
    result = proposal(study, start=4, end=4, selected_text="")
    updated = apply_passage(workspace, manuscript["id"], result["proposal"]["id"], expected_revision=1,
                            reviewer="Tester", replacement=" NEW")
    assert updated["manuscript"]["metadata"]["sections"][0]["text"].startswith("A 🧫 NEW measured β")


def test_two_editor_windows_cannot_overwrite_each_other(study):
    workspace, _, manuscript = study
    other = Workspace(workspace.root)
    revised = update_manuscript(other, manuscript["id"], expected_revision=1, title="New title")
    with pytest.raises(RuntimeError):
        update_manuscript(workspace, manuscript["id"], expected_revision=1, title="Old tab title")
    assert workspace.get_record(manuscript["id"]) == revised


def test_target_change_during_model_call_retains_failure_but_no_draft(study):
    workspace, source, manuscript = study

    class ChangingProvider:
        name = "test"
        is_remote = False

        def complete(self, messages, tools):
            update_manuscript(Workspace(workspace.root), manuscript["id"], expected_revision=1, title="Human changed title")
            return response(source)

    result = proposal(study, ChangingProvider())
    assert result["proposal"] is None
    assert result["run"]["status"] == "failed"
    assert result["run"]["error"]["code"] == "authoring_target_changed"
    assert workspace.get_record(manuscript["id"])["title"] == "Human changed title"
    assert workspace.get_run(result["run"]["id"])["status"] == "failed"


def test_stale_manuscript_rejects_apply_without_partial_approval(study):
    workspace, _, manuscript = study
    result = proposal(study)
    update_manuscript(workspace, manuscript["id"], expected_revision=1, title="Human revision")
    before_events = workspace.events()
    with pytest.raises(RuntimeError):
        apply_passage(workspace, manuscript["id"], result["proposal"]["id"], expected_revision=2, reviewer="Tester")
    assert workspace.events() == before_events
    assert workspace.get_record(result["proposal"]["id"])["review_status"] == "unreviewed"


def test_source_metadata_or_text_revision_change_invalidates_pending_proposal(study):
    workspace, source, manuscript = study
    result = proposal(study)
    workspace.update_record(source["id"], expected_revision=1, metadata={"external_allowed": False})
    with pytest.raises(RuntimeError):
        apply_passage(workspace, manuscript["id"], result["proposal"]["id"], expected_revision=1, reviewer="Tester")
    assert workspace.get_record(manuscript["id"]) == manuscript


def test_indirect_changed_source_rejects_apply(study):
    workspace, source, manuscript = study
    analysis = workspace.create_record("analysis", "Derived result", "Derived from three preparations.",
                                       metadata={"input_revisions": {source["id"]: 1}}, links=[source["id"]])
    result = proposal(study, ScriptedProvider([response(analysis)]), source_ids=[analysis["id"]])
    workspace.update_record(source["id"], expected_revision=1, content="Only two preparations.")
    with pytest.raises(RuntimeError):
        apply_passage(workspace, manuscript["id"], result["proposal"]["id"], expected_revision=1, reviewer="Tester")


def test_apply_cannot_create_circular_manuscript_evidence(study):
    workspace, _, manuscript = study
    commentary = workspace.create_record("note", "Review of manuscript", "A proposed review.", links=[manuscript["id"]])
    result = proposal(study, ScriptedProvider([response(commentary)]), source_ids=[commentary["id"]])
    before = workspace.export_bundle()
    with pytest.raises(ValueError, match="Circular"):
        apply_passage(workspace, manuscript["id"], result["proposal"]["id"], expected_revision=1, reviewer="Tester")
    after = workspace.export_bundle()
    assert all(after[key] == before[key] for key in ("records", "runs", "events"))


def test_remote_passage_requires_target_and_evidence_disclosure(study):
    workspace, source, manuscript = study
    source = workspace.update_record(source["id"], expected_revision=1, metadata={"external_allowed": True})
    provider = ScriptedProvider([response(source)], is_remote=True)
    result = proposal((workspace, source, manuscript), provider)
    assert result["run"]["error"]["code"] == "external_disclosure_not_allowed"
    assert provider.calls == []
    manuscript = update_manuscript(workspace, manuscript["id"], expected_revision=1, external_allowed=True)
    provider = ScriptedProvider([response(source)], is_remote=True)
    result = proposal((workspace, source, manuscript), provider)
    assert result["run"]["status"] == "needs_review"
    assert len(provider.calls) == 1


def test_reference_metadata_never_implies_full_text_read_and_does_not_disclose_it(study):
    workspace, source, _ = study
    reference = create_reference(workspace, title="Fictional paper", authors=["Example A"], year=2025,
                                 doi="https://doi.org/10.1234/example", full_text_ids=[source["id"]])
    assert reference["metadata"]["doi"] == "10.1234/example"
    assert reference["metadata"]["evidence_level"] == "bibliographic_metadata"
    assert source["content"] not in reference["content"]
    assert "does not establish that the paper was read" in reference["content"]
    updated = update_reference(workspace, reference["id"], expected_revision=1, year=None, abstract="Fictional abstract.")
    assert updated["metadata"]["year"] is None
    assert updated["metadata"]["evidence_level"] == "abstract_supplied"
    assert "Fictional abstract." in updated["content"]


@pytest.mark.parametrize("fields", [
    {"authors": "A scientist"}, {"year": True}, {"year": 25}, {"doi": "bogus"},
    {"url": "javascript:alert(1)"}, {"url": "https://user:secret@example.org/"},
    {"url": "https://exa mple.org/"}, {"external_allowed": "true"},
])
def test_reference_rejects_invalid_or_executable_bibliography_fields(tmp_path, fields):
    workspace = Workspace(tmp_path)
    with pytest.raises(ValueError):
        create_reference(workspace, title="Reference", **fields)
    assert workspace.list_records() == []


def test_manuscript_attached_figure_and_reference_revisions_are_bound(study):
    workspace, _, manuscript = study
    reference = create_reference(workspace, title="Reference")
    figure = workspace.create_record("output", "Synthetic figure", "<svg></svg>")
    sections = deepcopy(manuscript["metadata"]["sections"])
    sections[0].update(figure_ids=[figure["id"]], reference_ids=[reference["id"]])
    manuscript = update_manuscript(workspace, manuscript["id"], expected_revision=1, sections=sections)
    assert manuscript["metadata"]["input_revisions"] == {reference["id"]: 1, figure["id"]: 1}
    workspace.update_record(figure["id"], expected_revision=1, content="<svg>changed</svg>")
    with pytest.raises(RuntimeError):
        workspace.validate_current(manuscript["id"])
    # Explicit editor resave rebinds visible linked records after the scientist reloads.
    current = workspace.get_record(manuscript["id"])
    saved = update_manuscript(workspace, manuscript["id"], expected_revision=current["revision"], sections=sections)
    assert saved["metadata"]["input_revisions"][figure["id"]] == 2


def test_discussion_persists_evidence_bound_turns_without_implicit_history(study):
    workspace, source, _ = study
    discussion = create_discussion(workspace, title="Directions", focus="What should we measure next?")
    first = discuss(workspace, ScriptedProvider([response(source, "PRIVATE_PREVIOUS_ANSWER")]), discussion["id"],
                    expected_revision=1, question="PRIVATE_PREVIOUS_QUESTION", source_ids=[source["id"]], author="Scientist")
    provider = ScriptedProvider([response(source, "Second unreviewed proposal")])
    second = discuss(workspace, provider, discussion["id"], expected_revision=2, question="What alternatives?",
                     source_ids=[source["id"]], author="Scientist")
    calls = json.dumps(provider.calls)
    assert "PRIVATE_PREVIOUS_ANSWER" not in calls and "PRIVATE_PREVIOUS_QUESTION" not in calls
    assert len(second["discussion"]["metadata"]["turns"]) == 2
    assert first["discussion"]["metadata"]["turns"][0]["source_snapshots"][0]["record_id"] == source["id"]
    assert second["discussion"]["review_status"] == "unreviewed"
    reopened = Workspace(workspace.root)
    assert reopened.get_record(discussion["id"])["metadata"]["turns"] == second["discussion"]["metadata"]["turns"]


def test_discussion_selected_history_requires_every_current_evidence_source(study):
    workspace, source, _ = study
    discussion = create_discussion(workspace, title="Directions")
    first = discuss(workspace, ScriptedProvider([response(source)]), discussion["id"], expected_revision=1,
                    question="What next?", source_ids=[source["id"]], author="Scientist")
    turn_id = first["discussion"]["metadata"]["turns"][0]["id"]
    provider = ScriptedProvider([response(source)])
    with pytest.raises(ValueError, match="Reselect"):
        discuss(workspace, provider, discussion["id"], expected_revision=2, question="Elaborate", source_ids=[],
                author="Scientist", include_turn_ids=[turn_id])
    assert provider.calls == []
    included = discuss(workspace, provider, discussion["id"], expected_revision=2, question="Elaborate", source_ids=[source["id"]],
                       author="Scientist", include_turn_ids=[turn_id])
    assert "What next?" in json.dumps(provider.calls)
    assert included["discussion"]["metadata"]["turns"][-1]["included_turn_ids"] == [turn_id]
    source = workspace.update_record(source["id"], expected_revision=1, content="Corrected observations.")
    with pytest.raises(RuntimeError, match="Evidence changed"):
        discuss(workspace, ScriptedProvider([]), discussion["id"], expected_revision=3, question="Elaborate", source_ids=[source["id"]],
                author="Scientist", include_turn_ids=[turn_id])


def test_discussion_failure_is_persisted_and_concurrent_edit_never_overwritten(study):
    workspace, source, _ = study
    discussion = create_discussion(workspace, title="Directions")
    first = discuss(workspace, ScriptedProvider([]), discussion["id"], expected_revision=1,
                    question="What next?", source_ids=[source["id"]], author="Scientist")
    assert first["run"]["status"] == "failed"
    assert first["discussion"]["metadata"]["turns"][0]["status"] == "failed"

    class ChangingProvider:
        name = "test"
        is_remote = False

        def complete(self, messages, tools):
            workspace.update_record(discussion["id"], expected_revision=2, title="Human direction")
            return response(source)

    with pytest.raises(RuntimeError, match="changed"):
        discuss(workspace, ChangingProvider(), discussion["id"], expected_revision=2,
                question="What next?", source_ids=[source["id"]], author="Scientist")
    assert len(workspace.list_runs()) == 2
    assert len(workspace.get_record(discussion["id"])["metadata"]["turns"]) == 1
    assert workspace.get_record(discussion["id"])["title"] == "Human direction"


def test_remote_discussion_never_discloses_focus_without_authorization(study):
    workspace, source, _ = study
    source = workspace.update_record(source["id"], expected_revision=1, metadata={"external_allowed": True})
    discussion = create_discussion(workspace, title="Directions", focus="PRIVATE_FOCUS")
    provider = ScriptedProvider([response(source)], is_remote=True)
    result = discuss(workspace, provider, discussion["id"], expected_revision=1,
                     question="What next?", source_ids=[source["id"]], author="Scientist")
    assert provider.calls == []
    assert result["run"]["error"]["code"] == "external_disclosure_not_allowed"


@pytest.mark.parametrize("mutation", [
    lambda s: s.update(id="../../section"), lambda s: s.update(supplementary="false"),
    lambda s: s.update(extra="unrecognized"), lambda s: s.update(text="\ud800"),
    lambda s: s.update(text="text with \x01 control"),
    lambda s: s.update(figure_ids=["not-a-record"]),
])
def test_malformed_sections_do_not_leave_partial_updates(study, mutation):
    workspace, _, manuscript = study
    sections = deepcopy(manuscript["metadata"]["sections"])
    mutation(sections[0])
    before = workspace.export_bundle()
    with pytest.raises((ValueError, KeyError)):
        update_manuscript(workspace, manuscript["id"], expected_revision=1, sections=sections)
    after = workspace.export_bundle()
    assert all(after[key] == before[key] for key in ("records", "runs", "events"))


@pytest.mark.parametrize("sections", [None, "not sections", [{"id": "id-only"}], [None]])
def test_generic_editor_corruption_of_manuscript_is_readable_error(study, sections):
    workspace, source, manuscript = study
    changed = workspace.update_record(manuscript["id"], expected_revision=1,
                                       metadata={**manuscript["metadata"], "sections": sections})
    provider = ScriptedProvider([])
    with pytest.raises(ValueError):
        propose_passage(workspace, provider, changed["id"], expected_revision=changed["revision"],
                        section_id=manuscript["metadata"]["sections"][0]["id"], start=2, end=4,
                        selected_text="🧫", instruction="Refine", source_ids=[source["id"]])
    assert provider.calls == []


@pytest.mark.parametrize("turns", [None, "bad", [None], [{"id": "missing-fields"}], [
    {"id": "b" * 32, "question": None, "answer": "A", "author": "Scientist", "source_snapshots": []},
]])
def test_generic_editor_corruption_of_discussion_is_readable_error(study, turns):
    workspace, source, _ = study
    discussion = create_discussion(workspace, title="Directions")
    workspace.update_record(discussion["id"], expected_revision=1, metadata={**discussion["metadata"], "turns": turns})
    provider = ScriptedProvider([])
    with pytest.raises(ValueError):
        discuss(workspace, provider, discussion["id"], expected_revision=2, question="What next?",
                source_ids=[source["id"]], author="Scientist")
    assert provider.calls == []


@pytest.mark.parametrize("field,value", [
    ("selection", []), ("source_snapshots", "bad"), ("run_id", None),
])
def test_generic_editor_corruption_of_proposal_cannot_partially_apply(study, field, value):
    workspace, _, manuscript = study
    result = proposal(study)
    pending = result["proposal"]
    workspace.update_record(pending["id"], expected_revision=1, metadata={**pending["metadata"], field: value})
    with pytest.raises(ValueError):
        apply_passage(workspace, manuscript["id"], pending["id"], expected_revision=1, reviewer="Scientist")
    assert workspace.get_record(manuscript["id"]) == manuscript


@pytest.mark.parametrize("field,value", [("accepted_evidence_revisions", []), ("applied_proposals", "bad")])
def test_generic_editor_corruption_of_manuscript_audit_fields_cannot_apply(study, field, value):
    workspace, source, manuscript = study
    manuscript = workspace.update_record(manuscript["id"], expected_revision=1,
                                          metadata={**manuscript["metadata"], field: value})
    result = proposal((workspace, source, manuscript))
    with pytest.raises(ValueError):
        apply_passage(workspace, manuscript["id"], result["proposal"]["id"], expected_revision=2, reviewer="Scientist")
    assert workspace.get_record(manuscript["id"]) == manuscript


def test_source_change_after_model_run_is_preserved_but_no_proposal_written(study, monkeypatch):
    workspace, source, manuscript = study
    original_save_run = workspace.save_run

    def concurrent_save(run):
        saved = original_save_run(run)
        workspace.update_record(source["id"], expected_revision=1, content="Corrected evidence.")
        return saved

    monkeypatch.setattr(workspace, "save_run", concurrent_save)
    with pytest.raises(RuntimeError, match="Evidence changed"):
        proposal(study)
    assert workspace.get_record(manuscript["id"]) == manuscript
    assert workspace.list_records("note") == []
    assert len(workspace.list_runs()) == 1


def test_external_permission_revoked_during_call_prevents_second_disclosure(study):
    workspace, source, manuscript = study
    source = workspace.update_record(source["id"], expected_revision=1, metadata={"external_allowed": True})
    manuscript = update_manuscript(workspace, manuscript["id"], expected_revision=1, external_allowed=True)

    class RevokingProvider:
        name = "remote-test"
        is_remote = True
        calls = 0

        def complete(self, messages, tools):
            self.calls += 1
            update_manuscript(workspace, manuscript["id"], expected_revision=2, external_allowed=False)
            return tool_message("read_record", {"record_id": source["id"]})

    provider = RevokingProvider()
    result = proposal((workspace, source, manuscript), provider)
    assert provider.calls == 1
    assert result["run"]["status"] == "failed"
    assert result["proposal"] is None


def test_long_passage_and_instruction_reject_before_provider_request(study):
    provider = ScriptedProvider([])
    with pytest.raises(ValueError, match="5000"):
        proposal(study, provider, selected_text="x" * 5_001)
    with pytest.raises(ValueError, match="2000"):
        proposal(study, provider, instruction="x" * 2_001)
    assert provider.calls == []


def test_resaving_attachment_does_not_silently_refresh_accepted_prose_evidence(study):
    workspace, _, manuscript = study
    figure = workspace.create_record("output", "Figure", "The measured signal was 2.")
    result = proposal(study, ScriptedProvider([response(figure)]), source_ids=[figure["id"]])
    applied = apply_passage(workspace, manuscript["id"], result["proposal"]["id"], expected_revision=1, reviewer="Scientist")
    sections = deepcopy(applied["manuscript"]["metadata"]["sections"])
    sections[0]["figure_ids"] = [figure["id"]]
    workspace.update_record(figure["id"], expected_revision=1, metadata={"units": "corrected metadata"})
    current = workspace.get_record(manuscript["id"])
    with pytest.raises(RuntimeError, match="Input revision is stale"):
        update_manuscript(workspace, manuscript["id"], expected_revision=current["revision"], sections=sections)
    assert workspace.get_record(manuscript["id"]) == current
