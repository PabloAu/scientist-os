"""Independent cross-module round-trip checks for the authoring release."""

import httpx
import pytest
from docx import Document
from io import BytesIO

from scientist_os.literature import search_literature
from scientist_os.agent import AgentRunner
from scientist_os.providers import ScriptedProvider, tool_message
from scientist_os.publishing import (
    create_document_excerpt, create_presentation, export_manuscript, export_presentation, import_document,
)
from scientist_os.service import analyze
from scientist_os.studio import create_manuscript, create_reference
from scientist_os.workspace import Workspace


def test_every_returned_crossref_item_can_be_registered(tmp_path):
    payload = {"message": {"items": [{
        "title": ["A paper with a long supplied abstract"], "DOI": "10.1234/example",
        "abstract": "<p>" + "a" * 10_500 + "</p>",
    }]}}
    results = search_literature("public query", transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)))
    workspace = Workspace(tmp_path)
    for item in results["items"]:
        reference = create_reference(workspace, **item)
        if item["abstract"]:
            assert reference["metadata"]["evidence_level"] == "abstract_supplied"
        else:
            assert reference["metadata"]["evidence_level"] == "bibliographic_metadata"
            assert "Oversized or malformed abstracts are omitted" in results["notice"]


def test_valid_manuscript_section_title_round_trips_to_export(tmp_path):
    workspace = Workspace(tmp_path)
    manuscript = create_manuscript(workspace, title="Study", sections=[{"title": "A" * 210, "text": "Supported text."}])
    html = export_manuscript(workspace, manuscript["id"], format="html")
    assert b"A" * 210 in html


def test_manuscript_title_within_browser_limit_exports_to_word(tmp_path):
    workspace = Workspace(tmp_path)
    title = "A" * 280
    manuscript = create_manuscript(workspace, title=title)
    word = Document(BytesIO(export_manuscript(workspace, manuscript["id"], format="docx")))
    assert title in "\n".join(paragraph.text for paragraph in word.paragraphs)


def test_accepted_title_slide_body_can_be_exported(tmp_path):
    workspace = Workspace(tmp_path)
    try:
        presentation = create_presentation(workspace, title="Study", slides=[{
            "title": "Overview", "layout": "title", "body": "First\nSecond\nThird\nFourth\nFifth\nSixth",
        }])
    except ValueError as exc:
        assert "dense" in str(exc)
        assert workspace.list_records() == []
    else:
        assert export_presentation(workspace, presentation["id"]).startswith(b"PK")


def test_malformed_layout_is_readable_rejection_not_typeerror(tmp_path):
    workspace = Workspace(tmp_path)
    with pytest.raises(ValueError):
        create_presentation(workspace, title="Study", slides=[{"title": "Slide", "layout": []}])
    assert workspace.list_records() == []


def test_generic_reference_editor_error_is_readable_during_export(tmp_path):
    workspace = Workspace(tmp_path)
    reference = workspace.create_record("reference", "Reference", metadata={"authors": [42]})
    manuscript = create_manuscript(workspace, title="Study", sections=[{
        "title": "Results", "text": "A supplied result.", "reference_ids": [reference["id"]],
    }])
    with pytest.raises(ValueError):
        export_manuscript(workspace, manuscript["id"], format="html")


def test_valid_saved_figure_slide_body_exports_or_is_rejected_before_save(tmp_path):
    workspace = Workspace(tmp_path)
    data = workspace.create_record("dataset", "Synthetic data", "group,unit,value\nA,1,1\nA,2,2\nB,3,3\nB,4,4\n")
    result = analyze(workspace, {"dataset_id": data["id"], "method": "summary", "value_column": "value",
                                 "group_column": "group", "unit_column": "unit"})
    figure = result["output"]
    before = workspace.list_records()
    try:
        deck = create_presentation(workspace, title="Study", slides=[{
            "title": "Results", "layout": "evidence", "body": "\n".join(["A line"] * 12), "figure_id": figure["id"],
        }])
    except ValueError as exc:
        assert "dense" in str(exc)
        assert workspace.list_records() == before
    else:
        assert export_presentation(workspace, deck["id"]).startswith(b"PK")


def test_edited_source_prevents_both_manuscript_and_presentation_export(tmp_path):
    workspace = Workspace(tmp_path)
    dataset = workspace.create_record("dataset", "Synthetic data", "group,unit,value\nA,1,1\nA,2,2\nB,3,3\nB,4,4\n")
    result = analyze(workspace, {"dataset_id": dataset["id"], "method": "summary", "value_column": "value",
                                 "group_column": "group", "unit_column": "unit"})
    figure = result["output"]
    manuscript = create_manuscript(workspace, title="Study", sections=[{
        "title": "Results", "text": "A supplied result.", "figure_ids": [figure["id"]],
    }])
    deck = create_presentation(workspace, title="Study", slides=[{
        "title": "Results", "layout": "evidence", "figure_id": figure["id"],
    }])
    workspace.update_record(dataset["id"], expected_revision=1, content=dataset["content"].replace(",4\n", ",8\n"))
    with pytest.raises(RuntimeError):
        export_manuscript(workspace, manuscript["id"], format="html")
    with pytest.raises(RuntimeError):
        export_presentation(workspace, deck["id"])


def test_excerpt_from_large_private_document_is_the_only_disclosed_text(tmp_path):
    import json
    workspace = Workspace(tmp_path)
    document = import_document(workspace, filename="proposal.txt", data=(
        "🧫 A chosen observation.\n" + "PRIVATE_OMITTED_TEXT " * 2000
    ).encode("utf-8"))
    selected = "🧫 A chosen observation."
    position = document["content"].index(selected)
    start = len(document["content"][:position].encode("utf-16-le")) // 2
    excerpt = create_document_excerpt(workspace, document["id"], expected_revision=1,
                                       start=start, end=start + len(selected.encode("utf-16-le")) // 2,
                                       selected_text=selected, title="Chosen observation", external_allowed=True)
    assert document["metadata"]["external_allowed"] is False
    assert excerpt["content"] == selected and excerpt["metadata"]["input_revisions"] == {document["id"]: 1}
    provider = ScriptedProvider([
        tool_message("read_record", {"record_id": excerpt["id"]}),
        tool_message("finish", {"answer": "A supplied observation.", "citations": [{
            "record_id": excerpt["id"], "quote": selected, "sha256": excerpt["sha256"],
        }]}),
    ], is_remote=True)
    result = AgentRunner(workspace, provider).run("Check the chosen observation", [excerpt["id"]])
    assert result["status"] == "needs_review"
    assert "PRIVATE_OMITTED_TEXT" not in json.dumps(provider.calls)
    assert document["content"] not in json.dumps(provider.calls, ensure_ascii=False)


def test_excerpt_creation_verifies_original_bytes_and_exact_offsets(tmp_path):
    workspace = Workspace(tmp_path)
    document = import_document(workspace, filename="paper.txt", data="A 🧫 result.".encode("utf-8"))
    position = document["content"].index("🧫")
    start = len(document["content"][:position].encode("utf-16-le")) // 2
    with pytest.raises(ValueError, match="UTF-16"):
        create_document_excerpt(workspace, document["id"], expected_revision=1,
                                start=start, end=start + 1, selected_text="🧫", title="Excerpt")
    attachment = workspace.root / "attachments" / document["metadata"]["attachment_sha256"]
    attachment.write_bytes(b"changed bytes")
    with pytest.raises(RuntimeError):
        create_document_excerpt(workspace, document["id"], expected_revision=1,
                                start=start, end=start + 2, selected_text="🧫", title="Excerpt")
    assert workspace.list_records("source") == []
