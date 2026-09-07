# Scientist OS scientific procedures

Scientist OS uses a capable host's conversation and tools to carry out scientific project work. The installed [entry skill](../host-package/scientist-os/skills/scientist-os/SKILL.md) selects a small relevant procedure, executes authorized work and maintains portable project evidence. The scientist can start with an empty project, supply permitted material, ask an open question, correct assumptions, select an artifact and return later.

The scientific operating procedure is supplied as versioned Markdown and contracts. It includes meaningful human scientific gates that a program cannot decide. Read the [coverage matrix](WORKFLOW_COVERAGE.md) alongside the current host capability and journey verification reports; supplying a procedure does not establish that every host exercised it or every scientific output was reviewed.

The [initial host journeys](HOST_JOURNEY_OBSERVATIONS.md) and [fresh-context continuation](FRESH_RESUME_OBSERVATIONS.md) demonstrate Codex hosts using the installed skill, real reasoning, local tool execution and original-document vision on explicitly fictional material. They are simulated scientist requests, not a human usability study or scientific validation. The conversational segments exercised current editable product code; a separate installed-wheel check executed the committed pipeline, registered its numeric result, exported PNG, replayed exactly and rejected stale registration. The [final verification](PROTOTYPE_VERIFICATION.md) distinguishes these observations and records actual artifact inspection. Other hosts' capabilities remain unverified.

## Start instruction

> Use Scientist OS for this research project. Start or resume from its current context and decisions, inspect the permitted material I provide, and carry out the work I describe. Keep provenance, scientific uncertainty and pending decisions visible. Save enough project state to resume in a later conversation.

The host checks the installed interface through `scientist-os host --workspace <project-root> catalog`. It writes operation arguments to JSON, executes the appropriate services and records observations. [Host tools](../host-package/scientist-os/skills/scientist-os/references/host-tools.md) explains this boundary. Installing a skill does not create model/API credentials, connectors or equivalent tools on another host.

An explicitly permitted source/software folder outside the project is bound with `--permit-root <authorized-folder>` before the subcommand. The host records execution intent/completion and uses `task.reconcile_action` to account for uncertain outcomes after interruption; reconciliation is not automatic retry authorization.

## Integrated operations and observed use

| Work | Implemented support | Actual host observation and limit |
| --- | --- | --- |
| Start, converse and steer | `project.start/context/remember`, task/action journal, metadata/links/revision/freshness retrieval | Empty-project framing followed by a separate host's fresh-context continuation observed. Completed work was recovered without repetition; an external action with no receipt remained uncertain and was not retried. |
| Mixed sources and actual experiments | Scout/import with preserved bytes, scoped inspection, planned/actual scientific records and `science.reconcile` | Ten originals incorporated; PDF page and original PPTX slide visually inspected; fictional exposure correction and incomplete acquisitions retained. Unsupported binary remained uninspected. |
| Repaired extraction | `ingest.reextract` uses original attachment/hash plus expected revision, preserves identity/history and invalidates interpretation | Actual chart-workbook parser failure was repaired and re-extracted on the original PPTX. This does not imply universal Office/embedded-object support. |
| Versioned Python and native figures | Actual committed Python execution, archived inputs/config/environment/logs/QC, verification/replay; `analysis.register_result` selects a verified supported result JSON and binds its figure title | Original/corrected unit-level summaries and exact replay observed. A later installed-wheel run exercised the result bridge, PNG export, exact replay and rejection after source change. The fixture commit was subsequently pushed after exact generic-content inspection; historical run records retain their earlier remote-unverified status. |
| Controlled synthesis | Search/selection/extraction/comparability/freeze/synthesis/sensitivity records | Three generated independent effects pooled from five fictional reports, retaining duplicate and incompatible-effect exclusions; five sensitivity calculations observed. Fresh continuation repaired the historic figure-title binding, exported and visually inspected the forest PNG without resynthesis; its caption retains interval/fictional caveats. |
| Editable artifacts and correction | Draft manuscript/deck export, exact selected-passage revision, linked current/old evidence and stale checks | Editable drafts, passage revision and correction propagation observed; four old quantitative consumers rejected as stale. The exact final two manuscript pages, one proposal page, six presentation slides and comparison PNG were rendered and visually inspected. All remain scientifically unapproved. |
| Review and learning | Frozen baseline, atomic requests, accepted evidence revisions/stale checks, problem/fix records | A mock Methods clarification and new-experiment request were processed. Fresh continuation inspected the accepted evidence and re-bound request revisions while preserving baseline/history. The new-experiment decision and human consistency review remain open. Re-extraction and historic forest recovery were observed. |
| Scientific approval | Ordered scoped corpus transitions, inspectable check records and source-bound human decision fingerprints | Implemented checks are distinct from authenticating a human. The host did not advance all sources through all six states or claim approved-for-use status. |

Final observations close the earlier pending fresh-context, forest-export and current Office-layout checks; the original evaluator report remains a historical record. The installed wheel exposes 48 operations. The recorded complete local suite passed 521 Python tests and seven frontend checks, with Ruff passing. Those software checks support the specific mechanisms; they do not substitute for the separate conversational observations or a human scientific review. Local receipts are retained in `artifacts/installed-verification.json` and `artifacts/host-evaluation/visual-inspection-receipt.json`; generated research artifacts are excluded from public source archives.

## Procedure map

| Stages | Procedure | Meaningful deliverables and decisions |
| --- | --- | --- |
| 0 and throughout | [Authority and continuity](../host-package/scientist-os/skills/scientist-os/references/authority-continuity.md) | Goal/roles/scope, authority per question facet, attributed scientific decisions, living task state and correction/recovery. |
| 1 and re-entry | [Inventory and provenance](../host-package/scientist-os/skills/scientist-os/references/inventory-provenance.md) | Owner-described candidates, complete queues/cards, raw/derived census, scoped material/protocol facts, stable producer lineage and six readiness states. |
| 4 and throughout | [Corpus and ingestion](../host-package/scientist-os/skills/scientist-os/references/corpus-ingestion.md) | Six source states, exact original verification, topic/term/claim coverage, lawful acquisition, disjoint worker contracts and coordinator integration. |
| 2, 3, 5 | [Analysis and panels](../host-package/scientist-os/skills/scientist-os/references/analysis-panels.md) | Smallest contribution, hypotheses/controls, owning software/pins, exploratory/frozen analyses, full run record, QC/replay and nine-part panel gate. |
| 0, 4, 5, 6 | [Controlled meta-analysis](../host-package/scientist-os/skills/scientist-os/references/meta-analysis.md) | Defined eligibility/search, traceable study extraction, independence/comparability, frozen synthesis, sensitivity and bounded interpretation. |
| 6, 7 | [Writing and artifacts](../host-package/scientist-os/skills/scientist-os/references/writing-artifacts.md) | Editable proposal/article/deck/figures/supplement, exact selections, four writing reports, actual visual review, current venue checks and frozen submitted package. |
| 7, 8, 9 | [Review and learning](../host-package/scientist-os/skills/scientist-os/references/review-learning.md) | Atomic reviewer requests, least-expansive response and new-experiment necessity, clean/marked/response consistency, tested handoff and verified narrow procedure fixes. |

The stages are a dependency map with failure/re-entry rules. They are not a rigid wizard. A new dataset can re-open inventory and analysis while writing continues on unaffected evidence. A missing scientific decision blocks its dependent action; existing authorization still covers routine reversible work elsewhere.

## Portable templates

- [Project checkpoint](../host-package/scientist-os/skills/scientist-os/assets/project-checkpoint.template.json): active goal, input/artifact identities, decisions, completed/uncertain/pending actions and next safe step.
- [Ingestion run/handoff](../host-package/scientist-os/skills/scientist-os/assets/ingestion-run.template.json): disjoint scopes, state ceilings, actual source observations, coordinator checks and registry reconciliation.
- [Panel contract](../host-package/scientist-os/skills/scientist-os/assets/panel-contract.template.json): scientific question, methods/units/alternatives, claim bounds, cut criteria and nine evidence checks.
- [Scientific record contracts](../host-package/scientist-os/skills/scientist-os/assets/scientific-records.template.md): inventory, source/term/claim, run, decision, writing, reviewer and problem fields.

Templates are content contracts to populate from evidence; they are not Python operation requests and do not validate scientific adequacy. Use the installed operation catalog for executable schemas. Null/unknown values preserve missing facts; do not fill them with invented evidence or an assistant-generated human approval.

## Authority and reproducibility

Corpus-use approval, dataset readiness, artifact review, tool authorization and scientific validity are different properties. Exact quotations establish text integrity, not entailment. Scientific use needs the relevant source/analysis gates and an attributed scoped decision. The core's dependency mechanism only catches declared links; the host must reconcile undeclared effects when new evidence arrives.

For corpus approval, `project.remember` must record an actual human decision with exact `scope` and relevant `source_ids`, then `science.advance` uses its `decision_id`. The decision binds scientific source content/metadata and upstream identities; a matching scope alone cannot approve a different or changed source. Current context exposes scope freshness and permitted-use status. No API field authenticates a human statement or authorizes inventing one.

`review.request` similarly captures current revisions of its `evidence_ids`. A stale request requires renewed scientific assessment before update, while the submitted baseline stays frozen. Parser re-extraction can change interpretation and dependencies even when original bytes do not change. For fictional/simulation analyses, set run-level `synthetic=true` explicitly and retain planned-but-absent acquisition denominators separately from missing cells in present rows.

Execution records preserve selected inputs, software/environment/configuration, scientific choices, execution/failures and exact outputs, with declared numeric replay criteria. Host/model/procedure identity and relevant interaction observations are recorded where available. Equivalent LLM wording or identical cross-host behavior is not promised. Original research remains private and untouched; generic procedures and fictional fixtures are independent of that source material.
