"""Revision-bound authoring and discussion without implicit model disclosure.

Every model response is a proposal. Saving an edit records a human action but
does not approve its science. Bibliographic metadata never proves a paper read.
"""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from .agent import AgentError, AgentRunner, SourceScope
from .providers import Provider, redact
from .workspace import Workspace


_SECTION_ID = re.compile(r"^[0-9a-f]{32}$")
_UNSET = object()
DEFAULT_SECTIONS = ("Abstract", "Introduction", "Methods", "Results", "Discussion", "Supplementary material")


def _text(value: Any, name: str, maximum: int, *, empty: bool = True) -> str:
    if not isinstance(value, str) or len(value) > maximum:
        raise ValueError(f"{name} must be text within {maximum} characters")
    if any(ord(character) < 32 and character not in "\n\r\t" for character in value):
        raise ValueError(f"{name} contains unsupported control characters")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise ValueError(f"{name} must be valid Unicode text") from exc
    if not empty and not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _boolean(value: Any) -> bool:
    if type(value) is not bool:
        raise ValueError("external_allowed and supplementary must be booleans")
    return value


def _current(workspace: Workspace, record_id: str, expected_revision: int, kind: str, *, lineage: bool = False) -> dict:
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValueError("expected_revision must be a positive integer")
    record = workspace.validate_current(record_id) if lineage else workspace.get_record(record_id)
    if record["kind"] != kind:
        raise ValueError(f"Expected a {kind} record")
    if record["metadata"].get("studio_type") != kind:
        raise ValueError(f"This {kind} is not a structured studio record")
    if record["revision"] != expected_revision:
        raise RuntimeError("This record changed. Reload it before continuing.")
    return record


def _ids(workspace: Workspace, values: Any, kinds: set[str], name: str) -> tuple[list[str], dict[str, int]]:
    if not isinstance(values, list) or len(values) > 80 or any(not isinstance(v, str) for v in values):
        raise ValueError(f"{name} must be a bounded record-ID array")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must not contain duplicates")
    revisions = {}
    for record_id in values:
        record = workspace.validate_current(record_id)
        if record["kind"] not in kinds:
            raise ValueError(f"{name} refers to a record of the wrong kind")
        revisions[record_id] = record["revision"]
    return list(values), revisions


def _sections(workspace: Workspace, values: Any) -> tuple[list[dict], dict[str, int]]:
    if not isinstance(values, list) or not 1 <= len(values) <= 40:
        raise ValueError("A manuscript needs between 1 and 40 sections")
    result, revisions, seen = [], {}, set()
    for value in values:
        if not isinstance(value, dict) or set(value) - {"id", "title", "text", "figure_ids", "reference_ids", "supplementary"}:
            raise ValueError("Invalid manuscript section fields")
        section_id = value.get("id", uuid4().hex)
        if not isinstance(section_id, str) or not _SECTION_ID.fullmatch(section_id) or section_id in seen:
            raise ValueError("Sections need unique UUID hex identifiers")
        seen.add(section_id)
        figures, figure_revisions = _ids(workspace, value.get("figure_ids", []), {"output"}, "figure_ids")
        references, reference_revisions = _ids(workspace, value.get("reference_ids", []), {"reference"}, "reference_ids")
        revisions.update(figure_revisions)
        revisions.update(reference_revisions)
        result.append({"id": section_id, "title": _text(value.get("title"), "section title", 300, empty=False),
                       "text": _text(value.get("text", ""), "section text", 120_000),
                       "figure_ids": figures, "reference_ids": references,
                       "supplementary": _boolean(value.get("supplementary", False))})
    if sum(len(section["text"]) for section in result) > 120_000:
        raise ValueError("Total manuscript text exceeds 120,000 characters")
    return result, revisions


def _manuscript_content(title: str, sections: list[dict]) -> str:
    parts = [f"# {title}"]
    for section in sections:
        heading = section["title"] + (" [Supplementary]" if section["supplementary"] else "")
        parts.extend([f"## {heading}", section["text"]])
        if section["figure_ids"]:
            parts.append("Linked figures: " + ", ".join(section["figure_ids"]))
        if section["reference_ids"]:
            parts.append("Linked references: " + ", ".join(section["reference_ids"]))
    return "\n\n".join(parts)


def _accepted_evidence(metadata: dict) -> dict:
    evidence = metadata.get("accepted_evidence_revisions", {})
    if not isinstance(evidence, dict) or len(evidence) > 256:
        raise ValueError("Accepted manuscript evidence is malformed; repair it in the record editor")
    if any(not isinstance(key, str) or type(revision) is not int or revision < 1 for key, revision in evidence.items()):
        raise ValueError("Accepted manuscript evidence is malformed; repair it in the record editor")
    return evidence


def create_manuscript(workspace: Workspace, *, title: str, sections: list[dict] | None = None,
                      external_allowed: bool = False) -> dict:
    title = _text(title, "title", 1000, empty=False)
    if sections is None:
        sections = [{"title": heading, "supplementary": heading == "Supplementary material"} for heading in DEFAULT_SECTIONS]
    with workspace.transaction():
        sections, revisions = _sections(workspace, sections)
        return workspace.create_record("manuscript", title, _manuscript_content(title, sections), metadata={
            "studio_type": "manuscript", "studio_version": 1, "sections": sections,
            "external_allowed": _boolean(external_allowed), "input_revisions": revisions,
        }, links=list(revisions))


def update_manuscript(workspace: Workspace, record_id: str, *, expected_revision: int,
                      title: str | None = None, sections: list[dict] | None = None,
                      external_allowed: bool | None = None) -> dict:
    with workspace.transaction():
        record = _current(workspace, record_id, expected_revision, "manuscript")
        title = record["title"] if title is None else _text(title, "title", 1000, empty=False)
        sections, attached = _sections(workspace, record["metadata"].get("sections") if sections is None else sections)
        metadata = deepcopy(record["metadata"])
        # Evidence accepted from prior proposals stays revision-bound until the
        # scientist explicitly repairs/removes it through the record editor.
        evidence = _accepted_evidence(metadata)
        metadata.update(studio_type="manuscript", studio_version=1, sections=sections,
                        input_revisions={**attached, **evidence})
        if external_allowed is not None:
            metadata["external_allowed"] = _boolean(external_allowed)
        return workspace.update_record(record_id, expected_revision=expected_revision, title=title,
                                       content=_manuscript_content(title, sections), metadata=metadata,
                                       links=list(metadata["input_revisions"]))


def _selection(text: str, start: Any, end: Any, selected_text: Any) -> tuple[str, str]:
    """Translate DOM UTF-16 offsets, rejecting any half-surrogate boundary."""
    if type(start) is not int or type(end) is not int or start < 0 or end < start:
        raise ValueError("Selection offsets must be ordered nonnegative UTF-16 integers")
    selected_text = _text(selected_text, "selected text", 5_000)
    encoded = text.encode("utf-16-le")
    if end * 2 > len(encoded):
        raise ValueError("Selection extends beyond this section")
    try:
        before = encoded[:start * 2].decode("utf-16-le")
        selection = encoded[start * 2:end * 2].decode("utf-16-le")
        after = encoded[end * 2:].decode("utf-16-le")
    except UnicodeError as exc:
        raise ValueError("Selection splits a Unicode character") from exc
    if selection != selected_text:
        raise RuntimeError("Selected text no longer matches the saved section")
    return before, after


def _section(record: dict, section_id: str) -> dict:
    sections = record["metadata"].get("sections")
    if not isinstance(sections, list) or not sections or len(sections) > 40:
        raise ValueError("Manuscript section structure is invalid; repair it in the record editor")
    for section in sections:
        if not isinstance(section, dict) or not isinstance(section.get("id"), str):
            raise ValueError("Manuscript section structure is invalid; repair it in the record editor")
        if section["id"] == section_id:
            _text(section.get("text"), "section text", 120_000)
            _text(section.get("title"), "section title", 300, empty=False)
            return section
    raise ValueError("Section is not in this manuscript")


class _GuardedProvider:
    """Recheck the non-source passage/history disclosure before every request."""

    def __init__(self, workspace: Workspace, provider: Provider, target: dict, scope: SourceScope | None = None):
        self.workspace, self.provider, self.target = workspace, provider, target
        self.scope = scope
        self.name = getattr(provider, "name", "unknown")
        self.model = getattr(provider, "model", "unspecified")
        self.is_remote = getattr(provider, "is_remote", None)

    def check(self) -> None:
        if self.scope is not None:
            self.scope.check()
        try:
            current = self.workspace.validate_current(self.target["id"])
        except (RuntimeError, ValueError, KeyError):
            raise AgentError("authoring_target_stale") from None
        if current["revision"] != self.target["revision"]:
            raise AgentError("authoring_target_changed")
        if self.is_remote is True and current["metadata"].get("external_allowed") is not True:
            raise AgentError("external_disclosure_not_allowed")

    def complete(self, messages: list[dict], tools: list[dict]) -> dict:
        self.check()
        response = self.provider.complete(messages, tools)
        self.check()
        return response

    def redact(self, value: Any) -> Any:
        return getattr(self.provider, "redact", redact)(value)


def _check_snapshots(workspace: Workspace, snapshots: list[dict]) -> dict[str, int]:
    if not isinstance(snapshots, list) or len(snapshots) > 16:
        raise ValueError("Stored source snapshots are malformed")
    result = {}
    for snapshot in snapshots:
        if not isinstance(snapshot, dict) or not {"record_id", "revision", "sha256"} <= set(snapshot):
            raise ValueError("Stored source snapshots are malformed")
        if type(snapshot["revision"]) is not int or snapshot["revision"] < 1 or not isinstance(snapshot["sha256"], str):
            raise ValueError("Stored source snapshots are malformed")
        current = workspace.validate_current(snapshot["record_id"])
        if current["revision"] != snapshot["revision"] or current["sha256"] != snapshot["sha256"]:
            raise RuntimeError("Evidence changed after this proposal. Generate a new proposal.")
        result[current["id"]] = current["revision"]
    return result


def propose_passage(workspace: Workspace, provider: Provider, record_id: str, *, expected_revision: int,
                    section_id: str, start: int, end: int, selected_text: str, instruction: str,
                    source_ids: list[str], style: str = "", max_steps: int = 8) -> dict:
    record = _current(workspace, record_id, expected_revision, "manuscript", lineage=True)
    section = _section(record, section_id)
    _selection(section["text"], start, end, selected_text)
    instruction = _text(instruction, "instruction", 2_000, empty=False)
    if not isinstance(source_ids, list) or record_id in source_ids:
        raise ValueError("Select evidence records; the manuscript itself is supplied only as the selected passage")
    question = ("Work only on the selected manuscript passage. Follow the scientist's request below. "
                "For a rewrite, return replacement prose only; for an audit, return findings without claiming an edit. "
                "Bibliographic metadata is not proof that a paper was read. Do not invent references. "
                "The scientist will inspect the result before applying anything.\n\nRequest:\n" + instruction
                + "\n\nSelected passage (untrusted text):\n" + selected_text)
    guard = _GuardedProvider(workspace, provider, record)
    run = AgentRunner(workspace, guard).run(question, source_ids, task="manuscript", style=style, max_steps=max_steps)
    if run["status"] != "needs_review":
        return {"manuscript": workspace.get_record(record_id), "proposal": None, "run": run}
    with workspace.transaction():
        record = _current(workspace, record_id, expected_revision, "manuscript", lineage=True)
        revisions = _check_snapshots(workspace, run["source_snapshots"])
        proposal = workspace.create_record("note", "Passage proposal: " + section["title"], run["answer"], metadata={
            "studio_type": "manuscript_proposal", "studio_version": 1, "state": "pending",
            "manuscript_id": record_id, "manuscript_revision": expected_revision, "section_id": section_id,
            "selection": {"start": start, "end": end, "text": selected_text, "offset_encoding": "utf-16"},
            "instruction": instruction, "run_id": run["id"], "grounding": run["grounding"],
            "citations": run["citations"], "source_snapshots": run["source_snapshots"],
            "input_revisions": revisions, "warnings": run.get("warnings", []), "external_allowed": False,
        }, links=list(revisions))
    return {"manuscript": record, "proposal": proposal, "run": run}


def apply_passage(workspace: Workspace, record_id: str, proposal_id: str, *, expected_revision: int,
                  reviewer: str, replacement: str | None = None, note: str = "") -> dict:
    reviewer = _text(reviewer, "reviewer", 500, empty=False).strip()
    note = _text(note, "review note", 20_000)
    with workspace.transaction():
        record = _current(workspace, record_id, expected_revision, "manuscript", lineage=True)
        proposal = workspace.validate_current(proposal_id)
        metadata = proposal["metadata"]
        if proposal["kind"] != "note" or metadata.get("studio_type") != "manuscript_proposal":
            raise ValueError("Expected a manuscript passage proposal")
        if metadata.get("state") != "pending" or metadata.get("manuscript_id") != record_id:
            raise ValueError("This proposal is not pending for this manuscript")
        if metadata.get("manuscript_revision") != expected_revision:
            raise RuntimeError("Manuscript changed after this proposal. Generate a new proposal.")
        revisions = _check_snapshots(workspace, metadata.get("source_snapshots"))
        section = _section(record, metadata.get("section_id"))
        selection = metadata.get("selection")
        if not isinstance(selection, dict) or set(selection) != {"start", "end", "text", "offset_encoding"} or selection["offset_encoding"] != "utf-16":
            raise ValueError("Stored proposal selection is malformed")
        if not isinstance(metadata.get("run_id"), str) or not isinstance(metadata.get("citations"), list):
            raise ValueError("Stored proposal audit metadata is malformed")
        before, after = _selection(section["text"], selection["start"], selection["end"], selection["text"])
        replacement = proposal["content"] if replacement is None else _text(replacement, "replacement", 16_000)
        sections = deepcopy(record["metadata"]["sections"])
        for edited in sections:
            if edited["id"] == section["id"]:
                edited["text"] = before + replacement + after
        sections, attached = _sections(workspace, sections)
        manuscript_metadata = deepcopy(record["metadata"])
        evidence = {**_accepted_evidence(manuscript_metadata), **revisions}
        citations = manuscript_metadata.get("citations", [])
        for citation in metadata["citations"]:
            if citation not in citations:
                citations.append(citation)
        manuscript_metadata.update(sections=sections, accepted_evidence_revisions=evidence,
                                   input_revisions={**evidence, **attached}, citations=citations)
        applied_history = manuscript_metadata.setdefault("applied_proposals", [])
        if not isinstance(applied_history, list):
            raise ValueError("Manuscript edit history is malformed; repair it in the record editor")
        applied_history.append({
            "proposal_id": proposal_id, "run_id": metadata["run_id"], "reviewer": reviewer,
            "before_revision": expected_revision, "section_id": section["id"], "note": note,
            "human_edited": replacement != proposal["content"],
        })
        updated = workspace.update_record(record_id, expected_revision=expected_revision,
                                          content=_manuscript_content(record["title"], sections), metadata=manuscript_metadata,
                                          links=list(manuscript_metadata["input_revisions"]))
        proposal_metadata = {**metadata, "state": "applied", "applied_manuscript_revision": updated["revision"],
                             "applied_by": reviewer, "applied_text": replacement}
        proposal = workspace.update_record(proposal_id, expected_revision=proposal["revision"], metadata=proposal_metadata)
        proposal = workspace.review_record(proposal_id, expected_revision=proposal["revision"], decision="approved",
                                           reviewer=reviewer, note=note or "Accepted manuscript edit; scientific validity remains unreviewed.")
    return {"manuscript": updated, "proposal": proposal}


def _reference(workspace: Workspace, title: str, metadata: dict) -> tuple[str, dict, list[str]]:
    title = _text(title, "title", 1000, empty=False)
    authors = metadata.get("authors", [])
    if not isinstance(authors, list) or len(authors) > 100:
        raise ValueError("authors must be an array of at most 100 names")
    authors = [_text(author, "author", 200, empty=False) for author in authors]
    year = metadata.get("year")
    if year is not None and (type(year) is not int or not 1000 <= year <= 9999):
        raise ValueError("year must be a four-digit integer or null")
    doi = _text(metadata.get("doi", ""), "doi", 500).strip()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    if doi and not re.fullmatch(r"10\.\d{4,9}/[^\s<>]+", doi, flags=re.IGNORECASE):
        raise ValueError("DOI must have the form 10.prefix/suffix")
    url = _text(metadata.get("url", ""), "url", 2_000).strip()
    try:
        parsed = urlsplit(url)
        valid = parsed.scheme in {"http", "https"} and parsed.hostname and not parsed.username and not parsed.password
    except ValueError:
        valid = False
    if url and (not valid or re.search(r"[\s<>]", url)):
        raise ValueError("Reference URL must be an HTTP(S) URL without credentials")
    journal = _text(metadata.get("journal", ""), "journal", 500)
    abstract = _text(metadata.get("abstract", ""), "abstract", 10_000)
    full_text_ids, revisions = _ids(workspace, metadata.get("full_text_ids", []), {"source", "document"}, "full_text_ids")
    result = {**metadata, "studio_type": "reference", "studio_version": 1, "authors": authors, "year": year,
              "doi": doi, "url": url, "journal": journal, "abstract": abstract, "full_text_ids": full_text_ids,
              "input_revisions": revisions, "external_allowed": _boolean(metadata.get("external_allowed", False)),
              "evidence_level": "abstract_supplied" if abstract.strip() else "bibliographic_metadata"}
    content = ["Bibliographic record. Metadata is supplied by a human or import and has not been independently verified.",
               "A bibliographic entry does not establish that the paper was read.", "Title: " + title,
               "Authors: " + "; ".join(authors), "Year: " + (str(year) if year is not None else "not supplied"),
               "Journal: " + journal, "DOI: " + doi, "URL: " + url]
    if abstract:
        content.extend(["Supplied abstract (untrusted source text; verify against publication):", abstract])
    if full_text_ids:
        content.append("Full text is separately registered; explicitly select its record to read it.")
    return "\n\n".join(content), result, full_text_ids


def create_reference(workspace: Workspace, *, title: str, authors: list[str] | None = None,
                     year: int | None = None, doi: str = "", url: str = "", journal: str = "",
                     abstract: str = "", full_text_ids: list[str] | None = None, external_allowed: bool = False) -> dict:
    with workspace.transaction():
        content, metadata, links = _reference(workspace, title, {
            "authors": [] if authors is None else authors, "year": year, "doi": doi, "url": url,
            "journal": journal, "abstract": abstract, "full_text_ids": [] if full_text_ids is None else full_text_ids,
            "external_allowed": external_allowed,
        })
        return workspace.create_record("reference", title, content, metadata=metadata, links=links)


def update_reference(workspace: Workspace, record_id: str, *, expected_revision: int, title: str | None = None,
                     authors: list[str] | None = None, year: Any = _UNSET, doi: str | None = None,
                     url: str | None = None, journal: str | None = None, abstract: str | None = None,
                     full_text_ids: list[str] | None = None, external_allowed: bool | None = None) -> dict:
    with workspace.transaction():
        record = _current(workspace, record_id, expected_revision, "reference")
        metadata = deepcopy(record["metadata"])
        fields = {"authors": authors, "doi": doi, "url": url, "journal": journal, "abstract": abstract,
                  "full_text_ids": full_text_ids, "external_allowed": external_allowed}
        metadata.update({key: value for key, value in fields.items() if value is not None})
        if year is not _UNSET:
            metadata["year"] = year
        title = record["title"] if title is None else title
        content, metadata, links = _reference(workspace, title, metadata)
        return workspace.update_record(record_id, expected_revision=expected_revision, title=title,
                                       content=content, metadata=metadata, links=links)


def create_discussion(workspace: Workspace, *, title: str, focus: str = "", external_allowed: bool = False) -> dict:
    title = _text(title, "title", 1000, empty=False)
    focus = _text(focus, "focus", 2_000)
    return workspace.create_record("discussion", title, "Research discussion: " + title + "\n\n" + focus, metadata={
        "studio_type": "discussion", "studio_version": 1, "focus": focus, "turns": [],
        "external_allowed": _boolean(external_allowed),
    })


def discuss(workspace: Workspace, provider: Provider, record_id: str, *, expected_revision: int,
            question: str, source_ids: list[str], author: str, include_turn_ids: list[str] | None = None,
            style: str = "", max_steps: int = 8) -> dict:
    record = _current(workspace, record_id, expected_revision, "discussion", lineage=True)
    question = _text(question, "question", 3_000, empty=False)
    author = _text(author, "author", 500, empty=False)
    turns = record["metadata"].get("turns")
    if not isinstance(turns, list) or any(not isinstance(turn, dict) for turn in turns):
        raise ValueError("Discussion history is malformed; repair it in the record editor")
    seen_turn_ids = set()
    for turn in turns:
        if not {"id", "source_snapshots", "question", "answer", "author"} <= set(turn):
            raise ValueError("Discussion history is malformed; repair it in the record editor")
        _text(turn["id"], "turn ID", 32, empty=False)
        if not _SECTION_ID.fullmatch(turn["id"]) or turn["id"] in seen_turn_ids:
            raise ValueError("Discussion history contains invalid or duplicate turn IDs")
        seen_turn_ids.add(turn["id"])
        _text(turn["question"], "stored question", 3_000)
        _text(turn["answer"], "stored answer", 20_000)
        _text(turn["author"], "stored author", 500, empty=False)
    focus = _text(record["metadata"].get("focus"), "focus", 2_000)
    if len(turns) >= 50:
        raise ValueError("Discussion has 50 turns; start a new discussion")
    include_turn_ids = [] if include_turn_ids is None else include_turn_ids
    if not isinstance(include_turn_ids, list) or len(include_turn_ids) > 5 or any(not isinstance(v, str) for v in include_turn_ids):
        raise ValueError("Select at most five prior turn IDs")
    if len(set(include_turn_ids)) != len(include_turn_ids):
        raise ValueError("Repeated prior turn ID")
    if not isinstance(source_ids, list) or record_id in source_ids:
        raise ValueError("Select source records; include discussion history only by turn ID")
    # Prior assistant text is disclosed only after the scientist explicitly
    # reselects all evidence used for those turns. It remains untrusted context.
    selected = SourceScope(workspace, source_ids, require_external=getattr(provider, "is_remote", False) is True)
    history = []
    by_id = {turn["id"]: turn for turn in turns}
    for turn_id in include_turn_ids:
        if turn_id not in by_id:
            raise ValueError("Prior turn does not belong to this discussion")
        turn = by_id[turn_id]
        snapshots = turn["source_snapshots"]
        if any(snapshot["record_id"] not in selected.records for snapshot in snapshots):
            raise ValueError("Reselect every evidence record used by the included prior turns")
        _check_snapshots(workspace, snapshots)
        history.append({"question": turn["question"], "answer": turn["answer"], "status": "unreviewed prior context"})
    history_text = json.dumps(history, ensure_ascii=False)
    if len(history_text) > 3_000:
        raise ValueError("Selected history exceeds 3,000 characters; include fewer turns")
    prompt = ("Discuss research directions with the scientist. Distinguish current observations, hypotheses, "
              "alternative interpretations, possible experiments, and decisions. Use only the explicitly selected evidence. "
              "The state of the field is unknown unless published literature evidence was selected. Bibliographic metadata "
              "alone does not prove a paper was read. Earlier conversation is unreviewed context, not evidence.\n\n"
              + "Focus: " + focus + "\nPrior turns: " + history_text + "\nQuestion: " + question)
    if len(prompt) > 8_000:
        raise ValueError("Discussion context exceeds the model request bound; shorten focus or selected history")
    guard = _GuardedProvider(workspace, provider, record, scope=selected)
    run = AgentRunner(workspace, guard).run(prompt, source_ids, task="experiment", style=style, max_steps=max_steps)
    with workspace.transaction():
        current = _current(workspace, record_id, expected_revision, "discussion")
        if run["status"] == "needs_review":
            _check_snapshots(workspace, run["source_snapshots"])
        metadata = deepcopy(current["metadata"])
        metadata["turns"].append({
            "id": uuid4().hex, "author": author, "question": question, "answer": run.get("answer", ""),
            "run_id": run["id"], "status": run["status"], "review_status": "unreviewed",
            "grounding": run["grounding"], "citations": run["citations"], "source_snapshots": run["source_snapshots"],
            "warnings": run.get("warnings", []), "error": run.get("error"), "included_turn_ids": include_turn_ids,
        })
        if len(json.dumps(metadata, ensure_ascii=False).encode("utf-8")) > 220_000:
            raise ValueError("Discussion storage limit reached; start a new discussion. The model run was preserved.")
        transcript = ["Research discussion: " + current["title"], metadata["focus"], "All assistant turns are unreviewed proposals."]
        for turn in metadata["turns"]:
            transcript.extend([turn["author"] + ": " + turn["question"], "Assistant: " + (turn["answer"] or "[Run failed]")])
        updated = workspace.update_record(record_id, expected_revision=expected_revision,
                                          content="\n\n".join(transcript), metadata=metadata)
    return {"discussion": updated, "run": run}
