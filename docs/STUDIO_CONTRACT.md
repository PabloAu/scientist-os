# Authoring studio API contract

`scientist_os.studio` implements module-level functions below. All return JSON-serializable dictionaries; rejected input raises `ValueError`, stale revisions/lineage raise `RuntimeError`, missing records raise `KeyError`. No function performs network lookup. Provider calls use the existing bounded `AgentRunner` and an injected provider. HTTP routes remain the lead's ownership.

## Manuscripts

- `create_manuscript(workspace, *, title, sections=None, external_allowed=False) -> record`
- `update_manuscript(workspace, record_id, *, expected_revision, title=None, sections=None, external_allowed=None) -> record`
- `propose_passage(workspace, provider, record_id, *, expected_revision, section_id, start, end, selected_text, instruction, source_ids, style='', max_steps=8) -> {manuscript, proposal, run}`
- `apply_passage(workspace, record_id, proposal_id, *, expected_revision, reviewer, replacement=None, note='') -> {manuscript, proposal}`

Manuscript metadata: `studio_type: 'manuscript'`, `studio_version: 1`, `sections: [{id, title, text, figure_ids, reference_ids, supplementary}]`, `external_allowed`, and generated `input_revisions` for linked figures/references. The record's content is a generated plain Markdown representation. A section ID is a UUID hex string (32 lowercase hex); omit `id` on a new section and the server assigns it. Sections retain IDs across saves and reorderings. `figure_ids` and `reference_ids` are record-ID arrays; figures must be output records, references reference records. `supplementary` is boolean. Maximum 40 sections and 120,000 aggregate text characters. Default sections: Abstract, Introduction, Methods, Results, Discussion, Supplementary material.

Passage offsets are **JavaScript UTF-16 code units**, matching textarea.selectionStart/selectionEnd. Half-surrogate offsets and mismatched `selected_text` are rejected. Empty exact selections support insertion. Only selected passage + instruction + explicitly selected evidence enter model context; the rest of the manuscript never enters implicitly. Remote providers also require the manuscript's explicit external_allowed flag, rechecked before every request. Once the agent runner starts, its outcome is persisted; proposal is a `note` record (or null on a failed model run), with `studio_type: 'manuscript_proposal'`, target manuscript/revision/section/selection and run ID. Its content is the proposed replacement. It is unreviewed and **never applied automatically**. Apply requires the unchanged manuscript revision, unchanged evidence revisions, and a named human reviewer. An optional human-edited replacement is supported. Applying records the decision but leaves the manuscript scientifically unreviewed. Source citations are traceability checks, not proof of claim support.

Passages are limited to 5,000 characters, instructions to 2,000, and optional human replacement text to 16,000. A failed request validation makes no provider call. When a concurrent edit is detected after a run, the run remains in activity and the studio save raises a readable conflict. Accepted proposal evidence is retained in `accepted_evidence_revisions` and `citations`: editing an attachment cannot silently refresh the evidence supporting accepted prose. If that evidence changes, the scientist must review the affected prose and explicitly repair its provenance in the generic record editor before further proposals or export. The original record versions remain in the event history.

## Reference library

- `create_reference(workspace, *, title, authors=None, year=None, doi='', url='', journal='', abstract='', full_text_ids=None, external_allowed=False) -> record`
- `update_reference(workspace, record_id, *, expected_revision, title=None, authors=None, year=None, doi=None, url=None, journal=None, abstract=None, full_text_ids=None, external_allowed=None) -> record`

Reference records store bibliographic fields in metadata plus `evidence_level: 'bibliographic_metadata'` or `'abstract_supplied'`. Bibliographic information does **not** claim the paper was read. `full_text_ids` only links separately registered source/document records; a model must explicitly select those records to read them. DOI and HTTP(S) URL syntax are validated, but no lookup or DOI resolution is claimed. A year is an integer or null. Authors are a string array. Updating year to null is supported by passing null explicitly.

## Research discussions

- `create_discussion(workspace, *, title, focus='', external_allowed=False) -> record`
- `discuss(workspace, provider, record_id, *, expected_revision, question, source_ids, author, include_turn_ids=None, style='', max_steps=8) -> {discussion, run}`

Discussion metadata: `studio_type: 'discussion'`, `focus`, `turns`, `external_allowed`. Each turn contains stable `id`, `author`, `question`, `answer`, `run_id`, `status`, `grounding`, `citations`, `source_snapshots`, `warnings`, and `included_turn_ids`. No implicit history is sent. Explicitly include up to five prior turn IDs; all their evidence must be reselected with unchanged revisions and current lineage. Full history remains viewable locally. Every model turn is unreviewed and separately auditable. Max 50 turns per discussion; start a new discussion when full. Missing literature is reported as missing evidence; the assistant has no implicit live-field awareness. On concurrent edits, the run is retained but no turn is appended to the changed discussion.

Questions are limited to 3,000 characters, focus to 2,000, and selected prior history to 3,000; the combined prompt must fit 8,000 characters. Oversize history is rejected without silent truncation. Historical turns retain their original evidence snapshots; they are records of past conversations, and are not represented as current scientific conclusions.
