# Scientific workflow preservation matrix

This matrix transfers the generic requirements of the completed workflow-preservation audit into the conversational Scientist OS package. It accounts for its ten lifecycle stages and all 53 detailed control rows. The private audit retains exact source file/line mappings; this public counterpart uses generic control IDs and excludes private paths, records, scientific assertions and source extracts. The preserved original was inspected read-only; no original helper code was copied for apparent parity.

**Scope of coverage:** `P` means a concrete procedure is supplied for a capable host to execute; `H` means scientific judgment or attributed human review remains necessary; `C` points to implemented code support with a narrower mechanical scope; `D` means the specifically described behavior was observed in a real host journey. These are independent properties, not grades. This matrix does not certify all controls as automatically enforced or scientifically validated. Actual execution, installation, host capabilities and journey results belong in their dedicated verification records.

Procedure references below use stable generic IDs found in the supplied files:

- [A — authority/continuity](../host-package/scientist-os/skills/scientist-os/references/authority-continuity.md)
- [I — inventory/provenance](../host-package/scientist-os/skills/scientist-os/references/inventory-provenance.md)
- [C — corpus/ingestion](../host-package/scientist-os/skills/scientist-os/references/corpus-ingestion.md)
- [P — analysis/panels](../host-package/scientist-os/skills/scientist-os/references/analysis-panels.md)
- [M — controlled meta-analysis](../host-package/scientist-os/skills/scientist-os/references/meta-analysis.md)
- [W — writing/artifacts](../host-package/scientist-os/skills/scientist-os/references/writing-artifacts.md)
- [R/L — review, handoff, learning](../host-package/scientist-os/skills/scientist-os/references/review-learning.md)
- [T — host tools/checkpoints](../host-package/scientist-os/skills/scientist-os/references/host-tools.md)

## Integrated implementation and demonstration evidence

The [initial host observations](HOST_JOURNEY_OBSERVATIONS.md) and [fresh-context continuation](FRESH_RESUME_OBSERVATIONS.md) document separate Codex evaluators using the installed procedure, real reasoning, local tools and original-source vision on simulated scientist requests with CC0 fictional material. The [final verification](PROTOTYPE_VERIFICATION.md) adds exact final artifact inspection and engineering evidence. A separate installed-wheel check executed the committed pipeline, registered its result, exported PNG, replayed exactly and rejected registration after source change. All scientific artifacts remained draft/unapproved. These distinct observations establish neither a human study, biological validation nor arbitrary-model parity; exact hidden backend model/settings were not exposed.

| Controls | Current code support | Observed behavior / unclosed boundary |
| --- | --- | --- |
| AUTH-01/02/04/06/08; SCI-12 | [host_state.py](../src/scientist_os/host_state.py), [host_tools.py](../src/scientist_os/host_tools.py): empty project, full metadata context, questions/decisions, task/action checkpoints | D: framing, authority map, competing explanations, scientific abstentions, pause and separate fresh-context continuation. Completed actions/calculations were not repeated; the missing external receipt remained uncertain without retry. |
| INV-01/02/07/10; COR-01/05 | [ingestion.py](../src/scientist_os/ingestion.py), host scientific records: stable originals, planned/actual facts, current revisions, transitive affected IDs and `ingest.reextract` | D: ten originals unchanged, original PDF/PPTX visually inspected, fictional plan/actual discrepancy, corrected dataset and four stale consumers. Unsupported binary uninspected; full raw modality and six dataset-readiness gates remain P/H. |
| COR-02/03/10/11/13; AUTH-05/08 | `HostState.advance_evidence` / `remember`: ordered scope stages, inspectable check fields, exact source-evidence fingerprint and decision revision | C: human corpus-use decision must bind `source_ids` and exact scope; changed content/metadata/upstream identities invalidate use. D: authority separation observed. No full six-stage or human approved-for-use journey demonstrated. |
| SCI-03/04/05/06; INV-08 | [execution.py](../src/scientist_os/execution.py): committed code, input/config/environment snapshots, logs/QC/output hashes, actual execution/verification/replay | D: original/corrected summaries, exact replay, independently recomputed arithmetic and actual plot vision. The fixture commit was later pushed after generic-content inspection; historic manifests retain earlier remote-unverified status. Scientific panel stays mapped/unapproved; complete producer-stability and nine-part promotion remain P/H. |
| SCI-09/10/11; SCI-04 | `HostTools._register_result`: verifies completed run/current evidence, exact selected result file/hash and supported figure semantics/title, then creates linked authoring records | C/D: a separate installed-wheel check exercised this bridge, PNG export, exact replay and refusal after deliberate evidence change. The earlier manual registration is not counted as that bridge proof. Scientific approval remains H. |
| Expanded controlled meta-analysis | [meta_review.py](../src/scientist_os/meta_review.py): review/eligibility/extraction/comparability/freeze/synthesis/sensitivity | D: five generated reports, duplicate/incompatible-estimand exclusion, traceable extraction, synthesis and five sensitivity calculations. Fresh continuation repaired historic title metadata, exported and viewed the forest with adjacent caveat caption without resynthesis. No real literature completeness or human approval demonstrated. |
| SCI-07/08/09/10/11; INV-10 | Host manuscript/presentation/exports, [studio.py](../src/scientist_os/studio.py), [publishing.py](../src/scientist_os/publishing.py) | D: editable drafts, exact passage revision, correction-linked current/old artifacts. Exact final two manuscript pages, one proposal page, six slides and comparison PNG were rendered and visually inspected. Agent layout inspection does not approve scientific content. |
| SCI-13; ORCH-06/07 | [governance.py](../src/scientist_os/governance.py): frozen baseline, atomic requests, `evidence_ids` revision capture and stale checks, problem/fix record | D: mock clarification, new-experiment abstention, parser recovery and fresh-host evidence inspection/rebinding with history retained. Human consistency/new-experiment decision and completed resubmission remain unclaimed. |
| ORCH-01/02/03/04/05/08; SCI-14 | Supplied C06/C07/L01–L04 and task/action mechanisms | P/C plus bounded D: separate fresh host resumed from durable state and installed package replayed a recorded calculation. Complete scientific multi-lane ingestion, whole-project procedural audit and independent cross-machine restoration remain unverified. |

The remaining baseline rows below describe the complete procedure coverage. The table above adds implementation and observed evidence only within its stated limits; it does not promote whole stages from a successful example.

Final software evidence reports 48 installed operations, 521 passing Python tests, seven passing frontend checks and Ruff success. Those checks are separate from host reasoning and visual observations. Exact local receipts are `artifacts/installed-verification.json` and `artifacts/host-evaluation/visual-inspection-receipt.json`; generated research/run artifacts are intentionally excluded from public source archives. The initial evaluator's pending items are historical: subsequent fresh-context and final-render evidence closes the bounded continuity/forest/layout work while human scientific decisions stay pending.

## Ten-stage backbone

| Stage | Preserved inputs/work/output/gate | Failure and re-entry | Successor / mode |
| --- | --- | --- | --- |
| 0 — Frame | Goal, scope, roles, confidentiality, resources, authority, current brief/decisions/status; known scope permits routine work and material scientific choices retain an owner. | Missing authority blocks dependent action; changed aims, resources, roles or evidence reopen framing. | A01–A05; P/H |
| 1 — Inventory | Complete candidate queues, owner descriptions, source identities, raw/derived separation, hierarchy, scoped cards, producer stability and linked uses. | Missing/conflicting facts stay unresolved; moving output stays processing-active; new material or changed scope re-enters. | I01–I06; P/H |
| 2 — Contribution | Smallest defensible question/narrative, essential/optional results, panel contracts, alternative explanations, prohibited claims and lead decision. | Unsupported/cut/contradictory panels reopen spine and downstream claims. | P01; P/H |
| 3 — Software | Owning repositories, immutable/pushed production identity, lock/config/seeds, representative numeric/visual replay and Methods reconciliation. | Dirty/remote-unverified code is labelled; discrepancy blocks production promotion and re-enters owning code. | P02, P05; P/H |
| 4 — Literature | Source identity/authority, six states, original checks, lawful gap search, topic/term/claim coverage and scoped use approval. | Inaccessible/ambiguous/conflicting evidence remains unverified; new source, scope or terms reopen mapping/use. | C01–C07; P/H |
| 5 — Analysis | Candidate observables → approved/frozen estimand/display → versioned Python → QC/missingness/uncertainty/alternatives/failure denominator → panel gate. | Retain failed runs; changed inputs/choices/QC reopen analysis; never tune confirmatory thresholds silently. | P03–P05; P/H |
| 6 — Communication | Evidence-ready section/panel drafting; coordinated Methods/figures/supplements; claim/citation/term/change reports; editable exact artifacts. | Precise missing-evidence placeholders and stale selection checks route back to owning stage. | W01–W04; P/H |
| 7 — Submission | Integrated science/statistics/provenance/accessibility/governance/current venue review; exact approved package and submitted manifest. | Unresolved facts, rights or approvals block affected release; changed artifacts require exact re-review. | W05; P/H |
| 8 — Transfer | Portable sources/access/state/procedure/run handoff; actual restoration/replay and verified scoped workflow improvements. | Missing assets/dependencies/access are explicit; failed restore is a problem, not a certified handoff. | L01–L04; P/H |
| 9 — Reviewer round | Immutable submitted intake, atomic requests, full inventory, least-expansive adequate response, necessity/approval for new work and clean/marked/response reconciliation. | Missing baseline stops editing; ambiguity, new evidence and deadline/resource conflicts reopen the appropriate decision/stage. | R01–R04; P/H |

## Entry, routing, memory and authority — 8 controls

| ID | Generic baseline control | Concrete successor | Coverage and practical boundary |
| --- | --- | --- | --- |
| AUTH-01 | Substantive-task preflight | A01; skill Start/resume | P: current context/status/plan/decisions/problems and controlling records; no requirement to load every private document. |
| AUTH-02 | Fast lookup versus scientific question | A01–A02 | P: narrow index lookup versus facet-specific scientific retrieval. |
| AUTH-03 | Answer states and answer contract | A03 | P/H: confirmed/bounded/provisional/unresolved/not-represented, criterion, evidence, conflict and smallest next check; exact quote status remains separate. |
| AUTH-04 | Controlling authority by facet | A02 | P: ten routes spanning status, literature, experimental facts, execution, readiness, writing and transfer. |
| AUTH-05 | Field-scoped source precedence | A03, I02–I03 | P/H: embedded acquisition properties versus contemporaneous conditions versus historical execution; explicit conflict ledger. |
| AUTH-06 | Current status, decisions and continuity | A04–A05, T | P/C/D: scoped decisions, metadata-bearing context, action checkpoints, correction impact and actual fresh-context recovery without repeating completed work or uncertain external actions. |
| AUTH-07 | Restricted model action boundary | Skill invariants, T, A04 | **Explicitly revised by the conversational build authorization:** host may operate permitted tools and make reversible drafts. Legacy [agent.py](../src/scientist_os/agent.py) stays narrow. Sources remain untrusted instructions; scientific approval is never inferred from tool success. P/H/C. |
| AUTH-08 | Human material scientific choices | A04, P03, R03 | P/H: actual scientist decides material estimand, exclusion, protocol applicability, central claim and experimental commitments; no repeated operational approval for routine authorized work. |

## Inventory and provenance — 10 controls

| ID | Generic baseline control | Concrete successor | Coverage and practical boundary |
| --- | --- | --- | --- |
| INV-01 | Stable identities and original preservation | I02–I03, C01 | P/C: [workspace.py](../src/scientist_os/workspace.py) records/revisions and [publishing.py](../src/scientist_os/publishing.py) original-byte attachments support registered scope; external storage needs actual inventory. |
| INV-02 | Dataset/material/protocol/processed-data/analysis/output chain | I03; scientific-record template | P/C: full scientific contract supplied; generic checked links alone do not enforce complete biological provenance. |
| INV-03 | Bidirectional scientific navigation | I03, I06 | P: upstream dependencies plus derived downstream-use reconciliation; not cyclic dependency edges. |
| INV-04 | Lead-first screening before raw access/identity allocation | I01 | P/H: reuse existing owner description/authorization; retain rejected candidate without new dataset/raw access, preserve historical IDs. |
| INV-05 | Review/active/deferred queues and workbook/details reconciliation | I01, I06 | P: explicit index rows/cards/dispositions and close-out reconciliation; arbitrary notes are not automatic queue validation. |
| INV-06 | Raw acquisition census and modality metadata | I02 | P: pinned adapter contract, field authority, copy-sensitive clocks, errors/warnings/denominator. Instrument-specific readers remain host/project dependent. |
| INV-07 | Scoped material/protocol applicability and history | I03 | P/H: literal scope, exact record/version, deviation, evidence precedence, applicability state and consolidated reusable questions. |
| INV-08 | Stable derived producer handoff | I04 | P/H: producer completion plus exact roots, two observations/interval, unchanged identity and cross-stage unit/header/denominator checks. A database freshness check is insufficient. |
| INV-09 | Six dataset readiness states | I05 | P/H: raw-inventory-active, provenance-pending, processing-active, analysis-ready, evidence-ready, closed-excluded with distinct gates. |
| INV-10 | Changed evidence invalidation and stale rejection | I06, P05, W03 | P/C: [workspace.py](../src/scientist_os/workspace.py) dependency invalidation and [studio.py](../src/scientist_os/studio.py) stale passage handling support declared links; host reconciles undeclared impacts. |

## Controlled corpus, terms and citations — 13 controls

| ID | Generic baseline control | Concrete successor | Coverage and practical boundary |
| --- | --- | --- | --- |
| COR-01 | Original/source and ingestion registries | C01, C03 | P/C: original-byte import plus coordinated manifest/status/topic/source records; registry agreement requires checks. |
| COR-02 | Six corpus states and use-specific promotion | C01 | P/C/H: ordered per-scope transitions with check records; actual human approval binds source IDs, evidence fingerprint and exact scope. Full human approval journey not demonstrated. |
| COR-03 | Publication versus author-context authority | C01, A02 | P/H: proposals/posters/decks/notes/software support intent/design/history; publication also requires fit verification. |
| COR-04 | Metadata is not a read paper | C01, C03 | P/C: bibliography/search records remain discovery, consistent with [literature.py](../src/scientist_os/literature.py). |
| COR-05 | Format-aware bounded extraction and original inspection | C02 | P: native/scanned/mixed PDF, table/figure/OCR checks, large-slide index, exact visual locators and unsupported fallback. Actual host tool inspection must be recorded. |
| COR-06 | Adaptive topic-centered batches | C03, C06 | P: coherent questions, complexity-sensitive sizing, coverage and continuation; no fixed file count. |
| COR-07 | Gaps, contradictory literature and acquisition trail | C03, C05 | P: recorded queries/dates/screening/acquisition/access outcomes, contrary evidence and explicit handoff. |
| COR-08 | Topic index and mapped-source coverage reconciliation | C03, C06 | P: every mapped source reconciles source/status/topic/term/evidence records; host semantic checks remain necessary. |
| COR-09 | Controlled term definitions/excluded meanings/every-source disposition | C04 | P/H: project versus field usage, aliases/limits/conflicts, adequate existing control or change candidate, scoped approval. |
| COR-10 | Claim evidence and can/cannot-support limits | C05 | P/H: direct/partial/contextual/contradictory/unsupported, exact claim scope/type/tier and alternative explanations. |
| COR-11 | Exact citation integrity and fit | C05, W01 | P/C/H: [workspace.py](../src/scientist_os/workspace.py) and [publishing.py](../src/scientist_os/publishing.py) support quote/hash checks; original context, numerics and scientific entailment require actual review. |
| COR-12 | Retrieve before writing and precise placeholders | C05, W01 | P: claim map and verified evidence first; unsupported facts get specific evidence/decision placeholders, not invented support. |
| COR-13 | Confidential source disclosure | Skill invariants, T, C01 | P/C: current host authorization/roots apply; legacy per-record remote checks remain in [agent.py](../src/scientist_os/agent.py). Neither implies host/network isolation or release rights. |

## Role orchestration and learning — 8 controls

| ID | Generic baseline control | Concrete successor | Coverage and practical boundary |
| --- | --- | --- | --- |
| ORCH-01 | Content scout and coherent run preview | C06; ingestion-run template | P: scope/profile/lanes/waves/ceilings/cost/continuation; respects actual intervention choice and existing routine authorization. |
| ORCH-02 | Disjoint worker lanes and coordinator integration | C06 | P: source ownership, validated required reads, worker derived-handoff-only writes, no nested worker delegation; host must actually supply execution. |
| ORCH-03 | Handoff contract and independent original checks | C06; ingestion-run template | P: real before/after hashes, limits/locators, coverage/terms/evidence, independent coordinator inspection. Worker assertions do not certify visual review or source immutability. |
| ORCH-04 | Durable batch/lane close-out registry | C07 | P: execution/source/state/visual/coverage/search/acquisition/problem/continuation/validation fields. Registry indexes evidence; it does not become evidence. |
| ORCH-05 | Context-limit recovery without state promotion | C07, A05 | P: partial locator checkpoint, honest state, resized continuation and no blind repeated oversized run. |
| ORCH-06 | Problem register and routine/material classification | L02 | P/H: cause/options/owner/verification, open/monitoring/needs-decision/resolved/accepted-limit; material changes need the appropriate scientist. |
| ORCH-07 | Verified fix to narrowest owning procedure | L03 | P/H: reproduce, causal diagnosis, representative fix/unaffected check, version/validate and applicability limits; unverified workaround remains a candidate. |
| ORCH-08 | Whole-project audit and plan reconciliation | L04 | P: stage/queue/card/corpus/term/software/panel/decision/review/restore checks and truthful status; checklist attestation alone is insufficient. |

## Analysis, communication, submission and handoff — 14 controls

| ID | Generic baseline control | Concrete successor | Coverage and practical boundary |
| --- | --- | --- | --- |
| SCI-01 | Processed-data/analysis contracts | I03, P03; scientific-record template | P: producer, estimand, hierarchy, transforms, assumptions, QC/sensitivity, permitted use and failures. |
| SCI-02 | Variable exploration before fit-for-purpose approval | P03 | P/H: compare candidates, declare data-informed choices, lead estimand/display decision, freeze and scoped re-entry. |
| SCI-03 | Independent-unit accounting | P03, M02 | P/C/H: [science.py](../src/scientist_os/science.py) supports bounded summaries/independence checks; hierarchy, pairing, longitudinal design and comparability remain explicit scientific inputs. |
| SCI-04 | Complete immutable software/run manifest | P02–P03; scientific-record template | P/C/D: recorded inputs/commit/dirty patch/environment/lock/config/seeds/command/time/logs/QC/outputs and actual exact replay observed; remote availability/environment reconstruction remain separate. |
| SCI-05 | Owning repositories, remote pins and Methods reconciliation | P02 | P/H: accessible exact production commit, local-only label if remote unverified, representative migration parity and owning docs; no private publication to satisfy a pin. |
| SCI-06 | Panel contract, readiness/cut states and nine-part gate | P01, P04; panel template | P/H: role/alternatives/claim bounds, idea→mapped→analysis-ready→review-ready→approved or cut, actual nine checks. |
| SCI-07 | Section/passage workflow and explicit application | W03 | P/C: [studio.py](../src/scientist_os/studio.py) revision-bound selected-passage infrastructure; actual actor/draft status remain distinct from human scientific review. |
| SCI-08 | Claim/citation/terminology/change reports | W01; scientific-record template | P: four review reports alongside scientific prose with operational meanings and unresolved questions. |
| SCI-09 | Assembled manuscript/figures/references/supplement | W02 | P/C: [publishing.py](../src/scientist_os/publishing.py) exports supply infrastructure; cross-artifact numerical/factual/Methods consistency requires inspection. |
| SCI-10 | Exact-artifact visual review and promotion | W04–W05 | P/H: actual renderer/file/hash/pages checked, defects fixed, separate scientific approval. Prior export/template QA does not certify a new artifact. |
| SCI-11 | Bibliography and presentation authoring | C02, W02–W04 | P/C: [studio.py](../src/scientist_os/studio.py) and [publishing.py](../src/scientist_os/publishing.py) plus host tools support editable artifacts; additional authoring does not substitute for evidence gates. |
| SCI-12 | Persistent direction discussion | A04–A05, P01 | P/H: competing hypotheses, predictions/controls, criteria, scientific decision queue, corrections and current context; host conversation is primary. |
| SCI-13 | Submission and reviewer-response package | W05, R01–R04 | P/C/H: frozen baseline, atomic requests, accepted evidence revision/stale checks plus full triage/necessity and clean/marked/response procedures. Mock intake/clarification/abstention observed; completed scientific approval/resubmission unclaimed. |
| SCI-14 | Reproducible transfer and restore | L01, T | P/C/D within limits: separate fresh-context recovery and installed-package exact replay observed; complete cross-machine/environment reconstruction remains unverified. Asset/access/version/omission and broader restore procedures remain supplied. |

## Expanded conversational requirements

| Requirement | Supplied successor | Verification boundary |
| --- | --- | --- |
| Empty-project conversation, action, steering and later resume | Skill Start/resume; A01/A05/T; project-checkpoint template | Requires an actual capable host journey; an empty JSON fixture is not conversational inference. |
| Open-ended Python on explicit datasets | P02–P05, T | Versioned user-suitable modules, true execution/replay and run artifacts; fixed calculators alone are insufficient. |
| Controlled meta-analysis | M01–M04 | Question/search/selection/extraction/comparability/freeze/synthesis/sensitivity and actual source checks; pooling test results are not a systematic review. |
| Professional editable multi-artifact work and selected refinement | W01–W04 | Actual generated and rendered output, exact selection and evidence reconciliation. |
| Changed evidence affecting claims/outputs | I06, A05, P05, M04, W03 | Mechanically declared dependencies plus host audit of unlinked consequences; preserve exact history. |
| Verified current host inference and tool execution | T; all procedures | Record actual host/model observation and outputs; scripted provider responses and development agents alone do not establish the installed scientific journeys. |

## Deliberate adaptations and limits

The conversational host now has broader authorized tool action than the old answer-only beta. This is an explicit product change; the protected scientific approval, source-authority, privacy and original-preservation boundaries remain. Routine reversible work does not require new permission at every lane/stage. Configurable intervention points preserve an explicitly chosen preference without inventing one.

Instrument-specific software pins, filesystem conventions, biological claims and private source locations are not portable requirements. Their scientific meanings are retained as modality-adapter, field-authority, producer-lineage, calibration/header/denominator and reproducibility contracts. No claim is made that all original instrument formats or private applications are integrated. Conditional third-party research helpers are optional host tools, not required runtime dependencies.

Procedural preservation is supplied in this package. Automated semantic enforcement, a scientist pilot, biological validation and equal capability across models/hosts are separate claims requiring evidence. Human scientific judgment, original visual checks, experimental fact confirmation and consequential external decisions cannot be replaced by a passed schema validator.
