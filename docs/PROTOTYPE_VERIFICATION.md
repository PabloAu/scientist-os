# Conversational prototype verification

Observed 7 September 2026. Software version 0.3.0b1. This record separates
implemented behavior, real host observations, automated checks and scientific
validation. The fixture contains invented CC0 material; no physical experiment,
human annotation study or substantive literature meta-analysis was performed.

## Actual host journeys

An independent Codex evaluator used the installed Scientist OS skill and real
authorized host inference to inspect sources, select tools, execute actions and
write nine scientist-facing responses. The first segment used editable Python
code during integration; a second evaluator started without its transcript and
continued from durable project state. Neither used a canned response provider.
Exact hidden model/backend settings and usage are not exposed by the host.

| Required journey | Observed result | Scope |
|---|---|---|
| Empty project and broad question | Project, scientific roles, scope, task, authority and open questions created from conversation | Unknown scientific choices remained unknown |
| Mixed research folder | Ten originals preserved; source text/locators indexed; original PDF page and PowerPoint slide actually viewed | Unsupported instrument binary/JSON extraction gaps retained; original chart workbook import repaired and re-extracted |
| Evolving experiment | Original 10 ms plan retained beside described 12 ms actual; material/protocol/experiment links and competing explanations recorded | Three preparations per condition; two planned measurements/preparation; five observed measurements/condition; no invented randomization |
| Versioned Python | Committed pipeline executed on explicit data, environment/config/QC/logs/hashes saved, exact replay verified | Means 8 and 4 nm; n=3 independent preparations/group; fixture recovery only |
| Controlled meta-analysis | Five supplied reports screened; duplicate and incompatible ratio excluded; three exact extractions frozen; synthesis plus five sensitivity calculations | DL estimate 2, Q=8, I²=75%, tau²=3; generated studies, no substantive review claim |
| Editable artifacts and selected revision | Manuscript, proposal, supplement, quantitative figure and deck generated; selected passage revised with history | Actual final DOCX/PPTX rendered and all pages/slides inspected; drafts remain unapproved |
| New evidence and correction | One-cell author correction preserved separately; stable dataset advanced; old consumers rejected as stale; rerun/replay and revised artifacts | Corrected mean becomes 4.6667, SEM 0.6667; same six preparations |
| Fresh-context continuity | Separate host recovered current state, verified sources/runs/exports, reconciled review evidence and completed pending forest export | No completed calculation repeated; missing external receipt stayed uncertain with no retry |
| Mock reviewer round and learning | Exact baseline frozen; atomic n/new-experiment requests; minimal Methods clarification; failure/fix procedure record | New-experiment choice and human consistency review intentionally remain unresolved |

Detailed evidence: [initial observations](HOST_JOURNEY_OBSERVATIONS.md) and
[fresh-context observations](FRESH_RESUME_OBSERVATIONS.md). Local canonical state
is under `workspaces/journey-evaluation`; full arguments, outputs, failures and
scientist-facing responses are under `artifacts/host-evaluation` and
`artifacts/fresh-resume`. These research/run directories are intentionally excluded
from public source archives. The public generator and
[journey instructions](../examples/conversational/journeys.md) recreate the input
exercise, not identical model wording.

## Artifact inspection

The lead rendered the exact exported manuscript (two pages), proposal (one page)
and presentation (six slides) using installed Word/PowerPoint 16.0 in read-only
mode. DOCX PDFs were rasterized with Poppler. All final pages/slides and the
quantitative PNG were visually inspected through the host. Text, numbers, axes
and legends were readable with no clipping/overlap observed. This is attributed
agent layout inspection, not human scientific approval.

| Exact exported artifact | SHA-256 |
|---|---|
| Manuscript r4 DOCX | `a1ce4dd42a02e83aee7a78b7f52be6baba1c8c105c9ffd047bd69aa7fd9653b0` |
| Proposal r2 DOCX | `51bb2927d9ae9d402d989f38e6e31ce4186695bbbcde392009104633b3b416e6` |
| Corrected six-slide PPTX | `80805b2ba7b7290684408a62a4685dda83349cb5dba31b255bb48015d21241db` |
| Corrected comparison PNG | `545c5290b85ce49f030d9abf5ed80a1772e51801a0147734bee68df93ca34064` |
| Recovered forest PNG | `df5c34d8b6585f7603273f9332b11719d9f032fe088ee127c436c0160c0217c8` |

Render and exact-byte inspection receipts are saved locally. Standalone raster
plots require their saved adjacent captions: independence, SEM versus confidence
intervals, units, fictional status and limitations are scientific content. Native
deck elements and manuscript text remain editable. The host's local file-preview
tool accepted artifact opening; automatic host selection/annotation event wiring
was not implemented or claimed. Exact passage/slide identifiers drive edits.

## Failures retained and repairs checked

- An ordinary PowerPoint chart's inert XLSX workbook was rejected by the old
  embedded-object rule. Narrow archive validation now allows bounded inert chart
  workbooks while rejecting macros/OLE/nested payloads. Actual original re-extraction
  succeeded without changing its bytes; numeric chart values still require inspection.
- Forest PNG export found a title binding mismatch. New synthesis records retain
  the question title. Fresh continuation repaired only the historic metadata after
  verifying the exact SVG title, exported and viewed the forest without resynthesis.
- Independent integration review reproduced stale scientific approval reuse,
  missing accepted reviewer-evidence revisions, module resolution outside the
  committed snapshot and directly selected excluded folders. Each was fixed and
  covered by a substantive regression. Explicit supersession also invalidates an
  earlier approval. No private original was accessed for those reproductions.
- Stale source/edit gates and a resume attempt before a running checkpoint failed
  as intended. Failures remain in the run/action history. Review choices requiring
  a scientist were not fabricated to produce a passing status.

## Engineering and installation

The complete local suite passed: 521 Python tests, including real stdio MCP
create/read/update checks, and seven frontend regression checks. Ruff passed.
Normal Windows process/pipe permissions were required for MCP subprocess tests.
Two upstream FastAPI/Starlette/httpx/AnyIO deprecation warnings remain; no test
failures resulted. This does not certify a new browser visual acceptance run.

The personal plugin was installed and refreshed through the official local Codex
CLI flow. The portable wheel includes its skill, eight references and templates.
The inspected wheel was installed with locked dependencies into a separate user
tool environment. Import resolved to `site-packages`, not the editable checkout.
The installed command exposed 48 scientific operations; it executed the committed
pipeline, registered the exact result JSON as a figure, exported PNG, passed exact
replay and rejected registration after a deliberate scientific-metadata change.
The receipt is `artifacts/installed-verification.json`. This complements the live
host journeys; it is not a second independent conversational quality evaluation.
Distribution hashes and final revision are recorded in the release handoff.
Cross-platform CI is a separate result; a local Windows pass does not establish
live conversational behavior on Linux or another host.

GitHub ownership and the existing public repository were verified before pushing
the four inspected generic fixture files. The pipeline revision is
`1ef9b228d7c422be56a5607041f30ab797b25d45`. Historical run records correctly retain
the narrower remote evidence available at their execution time; later publication
does not rewrite their manifests.

## Capability and scientific limits

The [host matrix](HOST_CAPABILITIES.md) identifies actual browsing, local execution,
vision, artifact generation, installation and continuity observations. The
[workflow matrix](WORKFLOW_COVERAGE.md) preserves all ten stages and 53 controls,
distinguishing procedures, mechanical checks, observed paths and human judgement.
Not every workflow branch has a real-host acceptance case.

No new paid model API or compute was used. Existing host account usage is not a
claim of zero cost. Other hosts/models, cloud connectors, large-scale ingestion,
automatic OCR/table recovery, hostile-code isolation, automatic cross-machine
restore, laboratory execution, scientific validity and human usability remain
unverified or outside this prototype. Original scientific sources remain private
and unchanged. Pablo supplied intent and constraints; agents supplied implementation,
fictional fixtures and engineering verification. No scientific approval is attributed
to him by this exercise.
