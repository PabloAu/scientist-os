# Publishing and project library API

`publishing.py` functions accept a `Workspace`; raise `ValueError` for invalid input,
`RuntimeError` for stale lineage/revisions or changed attachment bytes, and `KeyError`
for missing records. Export functions return bytes and do not mutate review state.

- `import_document(workspace, *, filename: str, data: bytes, title: str = '', category: str = 'document') -> dict`
  supports `.pdf`, `.docx`, `.pptx`, `.txt`, `.md`, `.csv` (20 MB max). Creates a
  `document` record with extracted text and explicit page/slide/paragraph locators.
  Metadata: `category`, `filename`, `media_type`, `attachment_sha256`, `attachment_bytes`,
  `extraction` (method, limitations, segment count), `external_allowed: false`.
  Original bytes live under workspace `attachments/<sha256>`; user filenames never
  become filesystem paths. Original-byte download verifies the digest.
- `attachment_bytes(workspace, record_id) -> tuple[bytes, str, str]` returns original
  bytes, sanitized filename, media type. Always serve as attachment, never inline.
- `create_document_excerpt(workspace, record_id, *, expected_revision: int, start: int, end: int, selected_text: str, title: str, external_allowed: bool = False) -> dict`
  registers a `source` with 1–20,000 characters of exact selected document text.
  Offsets use JavaScript UTF-16 code units; half-surrogate boundaries, mismatches,
  stale revisions and changed original attachment bytes are rejected. Metadata
  retains document ID/revision, original-byte hash, exact excerpt hash, offsets,
  extraction limitations and page/slide/paragraph/line locators. Excerpts are
  private by default; a human may explicitly permit only this excerpt to be sent
  to an external model. Long extracts over the 16,384-byte citation quote limit
  retain revision/hash/range provenance without a duplicate full quote.
- `create_presentation(workspace, *, title: str, slides: list[dict], source_ids: list[str] | None = None) -> dict`
- `update_presentation(workspace, record_id, *, expected_revision: int, title: str, slides: list[dict], source_ids: list[str] | None = None) -> dict`
  Each slide: `{id?, title, body?, notes?, figure_id?, reference_ids?, layout?}`.
  IDs are stable UUID-derived strings when omitted. Layout is `title`, `section`,
  `evidence`, or `two_column`. `body` is plain text, paragraph-separated; notes are
  plain text. Max 40 slides; title 110 chars, body 900 chars, notes 8000 chars.
  Title/section slides require short bodies. Figure/reference/source links are
  frozen as `input_revisions`; an edited ancestor blocks export until refreshed.
- `export_presentation(workspace, record_id) -> bytes` emits a 16:9 editable PPTX
  with native text and shapes, editable scientific plots, evidence footnotes, full
  reference details and record revisions in speaker notes. Unsupported/crowded
  figures or text fail explicitly instead of omitting content.
  Text layout is measured with a bundled metric font and padded for Office font
  substitution, then exported with explicit line breaks. Plots use native editable
  shapes, exact stored estimates/bounds and full-precision numbers in notes, with
  at most eight rows per slide. They are not flattened screenshots or Excel chart
  workbooks. Manuscript figures allow twelve rows and are rendered from the same
  numeric results to embedded PNGs; imported SVG/HTML is never executed.
- `export_manuscript(workspace, record_id, *, format: str = 'docx') -> bytes`
  accepts `docx` or `html`. Manuscript `metadata.sections` entries are
  `{id, title, text, figure_ids: [], reference_ids: [], supplementary: false}`.
  Uses registered reproducible figures, numbered bibliography and supplements.
  Includes actual current review status; exports are never implicit approval.

Original document extraction is a reading aid: no OCR, no semantic validation,
and no promise of faithful visual layout. Office imports extract text only and do
not execute macros, linked content, embedded objects or instructions. PDF imports
extract text from native text layers; scanned pages need a separate OCR workflow.
No import/export operation accesses the network or executes arbitrary user code.
Original attachments preserve all bytes, including confidential text and metadata;
record redaction does not scrub originals. Back up the entire stopped workspace,
including its `attachments` folder; JSON export alone is not an attachment backup.

Boundaries: Office ZIPs allow at most 3,000 members, 50 MB expanded data, 10 MB per
member, 250:1 compression, 12 MB XML and 200,000 XML elements. DTDs, entities,
symlinks, duplicate/traversing paths, macros, ActiveX and embedded Office objects
are rejected. PDF extraction allows 250 pages, a bounded object graph and 4 MB
decoded page streams. Active JavaScript/embedded-file PDFs and unsupported stream
filters are rejected. Parsing remains local single-user software, not an OS-level
sandbox for adversarial files.
The pypdf 6.17 decoder limits for Flate, LZW, RunLength, declared streams and stream
arrays are clamped to 4 MB before opening the PDF, including compressed object
streams; non-image text/font streams have a 32 MB aggregate budget. The decoder
configuration is serialized and restored afterward. This limits expansion, but
does not promise a hard process memory or wall-time sandbox.

Dependencies are portable open-source Python packages: python-pptx, python-docx,
pypdf, defusedxml, matplotlib and Pillow. Browser preview and actual Office exports
share the same registered records; Office rendering can vary by installed fonts.

Implementation references: [python-pptx shapes](https://python-pptx.readthedocs.io/en/latest/api/shapes.html),
[python-pptx text](https://python-pptx.readthedocs.io/en/stable/user/text.html),
and [pypdf extraction and memory limits](https://pypdf.readthedocs.io/en/5.9.0/user/extract-text.html).

## Validation for the authoring beta

The publishing tests cover original-byte retention and tampering, private source
excerpts, UTF-16 selection boundaries, encrypted/active PDFs, compressed expansion,
Office archive traversal/entities/embedded objects, slide order, editable numeric
plots and notes, units/uncertainty, stale lineage, DOCX/HTML figures/references/
supplements and safe HTML escaping. Separate authoring audit tests cover schema
compatibility with the manuscript studio and generic record editor.

On Windows, a four-slide fictional deck was rendered through installed PowerPoint
and a one-page fictional manuscript through installed Word plus bundled Poppler.
Every resulting slide/page image was inspected after the final layout corrections:
no clipping, overlapping text, unwanted theme shadows or title rules remained.
This verifies these fixtures in those installed Office applications; it is not a
claim that every possible author input or Office/font combination was rendered.
The runtime itself requires neither PowerPoint nor Word and makes no Office COM
calls. The inspection artifacts stay in the ignored local `artifacts` directory.
