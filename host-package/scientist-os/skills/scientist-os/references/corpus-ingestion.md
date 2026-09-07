# Controlled corpus and adaptive ingestion

Stage 4 turns mixed source material into governed, use-specific evidence. Its inputs are the research question, topic/term gaps, source inventory and current claim/panel map. Its outputs are synchronized source/status/topic/term/evidence registries and exact verification records. Scientific-use decisions are scoped; neither registering a paper nor extracting a quotation approves the paper for every claim.

## C01 — Source identity, authority and six states

Preserve original bytes and stable source IDs, checksum or declared pending hash, origin/acquisition date, citation/publication status, format, parser/version, extraction quality, confidentiality/rights and original page/slide locators. Keep source manifest, ingestion status and topic/source-record indices reconciled. Record corrections, retractions or preprint/published-version relationships when relevant and verified.

| State | Required evidence | Does not establish |
| --- | --- | --- |
| `registered` | Located original or explicitly metadata-only candidate; identity/rights status recorded | Contents read or source acquired |
| `classified` | Actual type, subject, publication/authority class and permitted context role assessed | Extraction quality or scientific support |
| `extracted` | Bounded text/tables/figures, parser and quality/failures, exact original locators | Correct visual interpretation or support |
| `mapped` | Topics, term disposition and claim-evidence rows linked; gaps/conflicts recorded | Original verification |
| `verified` | Exact original passages/visuals inspected for the relevant claim, qualifiers, values and authority | Universal use approval |
| `approved-for-use` | Attributed scientific approval tied to source revision, claim/term, wording/use and limits | Approval for a different claim, version, artifact or disclosure |

Metadata-only search results can be registered/classified as such; they cannot be called extracted full text. Proposals, posters, presentations, notes and software docs establish author intent, design or history within their scope. They are not independent experimental validation. Published/preprint work requires original-source fit checks too; publication alone is not sufficient support.

The installed `science.advance` operation enforces ordered progress separately for each exact `scope`. Supply inspectable check evidence rather than booleans: `classification`; then `extraction_method` and `locators`; then `claim_or_term` and `support_limit`; then `original_checked`, `authority_checked` and `conflicts_checked`. These fields record checks; the host still has to perform them. For `approved-for-use`, first record the actual scientist's decision using `project.remember` with matching `scope` and `source_ids=[the_source_id]`, then pass its `decision_id`. Do not create a nominal human decision because the operation demands one.

The decision and progression bind an evidence fingerprint covering source identity/content, scientific metadata, links and upstream revisions, while excluding corpus-progress bookkeeping. This avoids circular invalidation from the act of recording a transition. A changed source, interpretation, upstream dependency or decision can make the previous scope stale. Inspect `corpus_scope_freshness` and `permitted_for_use` in current context; a historical `approved-for-use` label alone is insufficient. Re-enter mapping/verification and obtain a new source-bound approval where required. The host journey demonstrated useful ingestion and authority routing without traversing all six states; it did not demonstrate human use approval.

## C02 — Format-aware inspection

Scout format/size/content before selecting tools. Native text PDF: bounded page extraction plus rendered inspection of cited pages, tables, equations and figures. Scanned/mixed PDF: identify pages needing OCR, retain OCR uncertainty and compare relied-upon values/text to the original. DOCX/PPTX: inspect text structure, notes/comments/changes and embedded assets as applicable; record omissions. Large decks: first index slide numbers/titles, dimensions/media inventory and selected content; inspect relevant original slides at useful resolution rather than loading the whole deck or rasterizing everything without a need.

Preserve differences between `extracted_locators` and `visually_inspected_locators`, tool/version, inspection date, artifact hash and observation. A worker attestation or image filename does not prove someone viewed it. If unavailable or unsupported, retain a precise handoff with source ID, page/slide, required check and authority needed. Do not advance verified state from text alone when the relied-upon claim depends on a visual/table.

After a verified parser fix, `ingest.reextract(record_id, expected_revision)` checks the unchanged preserved attachment hash and retries extraction from those bytes. It retains the stable source identity and old history, creates a new extraction snapshot, resets scoped corpus progress and reports affected records. Revisit interpretation and dependent claims even when original bytes are unchanged. Re-extraction is not new source evidence or proof that every embedded object was understood.

An observed native-chart PPTX recovery established only bounded inert chart-workbook acceptance and slide-text re-extraction for the exercised fixture. Chart values still need original-slide vision; macro/OLE/nested payloads and unsupported instrument binaries remain outside that result. Large or unsupported files use an explicit host/domain-reader handoff, not an invented successful extraction.

## C03 — Topic batches, gaps and lawful acquisition

Use coherent question/topic batches sized to source complexity and useful coverage, not an arbitrary fixed file count. Assess whether the evidence answers the question, exposes conflict or requires continuation. Search for competing/negative explanations as well as support. Record databases/sites, full query, date, scope, screening criteria, hits considered, exclusions, acquisition attempts/outcomes and remaining gaps. Bibliographic metadata is a lead; inspect lawful original full text where needed. For inaccessible originals, use a permitted repository/publisher copy or ask for the specific source/section; record access status instead of fabricating extraction or bypassing access controls.

Reconcile every mapped source with topic and source-record indices, ingestion state, term disposition and evidence rows. A batch can close `adequate`, `gap-found` or `continuation-required`; adequacy is question-specific, not a claim that all literature has been found.

## C04 — Controlled terminology

For each concept retain preferred term, operational definition, field usage versus project usage, aliases, excluded meanings, measurement/model limits, exact supporting/conflicting sources and approval scope. Reconcile every ingested source: new term candidate, refinement/conflict, or adequate existing control with rationale. No forced new terminology entry when the existing control is sufficient. A scientific meaning change needs the lead's decision; routine spelling/style alignment does not. Propagate a changed definition to affected claims, captions, Methods, slides and searches.

## C05 — Claim evidence and citations

A claim-evidence row contains exact claim/version, claim type, scope, evidence tier, source/version/locator, support relation (`direct`, `partial`, `contextual`, `contradictory`, `unsupported`), what it can/cannot support, alternatives, qualifiers and state/owner. Split compound claims when their support differs. Distinguish source quotation integrity from entailment of the surrounding claim.

Before writing, retrieve the controlling evidence; inspect original source and relevant surrounding context, numerical/table values, limitations and contrary evidence. Verify citation identity/version, quote accuracy, exact claim fit, publication status and reviewed terms. Where insufficient, return a precise placeholder naming the missing fact/evidence/check rather than inventing citation-backed prose. A conflicting source creates a conflict row and impact review; it must not disappear because another source supports the desired narrative.

## C06 — Scout, plan, delegate, integrate

Use native host agents only when available and authorized. Sequential execution uses the same contracts. Development agents used to build Scientist OS do not demonstrate this scientific ingestion workflow.

The coordinator scouts content first, proposes one coherent run plan and carries out routine authorized work. Record intervention policy (`routine-authorized`, `approve-once`, `approve-each-wave`, or `approve-each-lane`) from existing task authorization/user preference; do not invent a preference or demand new approval for already-authorized reversible ingestion. Material scientific promotion remains separately gated. Plan includes profile, question, source scope, work/outputs, lanes/waves, state ceilings, relative cost, independent checks and continuation boundaries. Change the plan if content complexity warrants it.

Assign disjoint source IDs and read-only source scope to workers. Validate required paths before dispatch: resolve against the permitted project/source root, reject traversal/absolute escape where repository-relative paths are required, and verify referenced records exist. Workers may read only assigned sources and necessary shared context, write only their explicit derived handoff path, and may not delegate further or update shared registries. Coordinator alone integrates canonical changes. These role instructions are not a sandbox; inspect actual tool/file evidence within the host's permission boundary.

Worker handoff includes lane/run identity, actual source IDs, before/after original hashes, extraction/proposed states, topic mappings, linked records, exact locators, visual observations, authority boundaries, term dispositions, evidence rows, coverage/search/acquisition disposition, blockers/problems, continuation boundary, skill-learning disposition and proposed integration. No state exceeds its ceiling (`mapped` or `verified`); workers never grant human scientific approval. Resolve provisional pending hashes to actual 64-hex digests before immutable comparison.

Coordinator checks ownership, existence, path boundaries, unchanged originals, ceiling, required fields and locator validity, then independently opens representative originals and checks scientific fit. Verify all high-impact or conflicting extracts rather than relying only on a random spot check. Self-report and schema validation alone cannot justify verified state. Integrate source/status/topic/term/evidence/project links consistently; run mechanical validators and inspect semantic agreement. Reject incomplete/conflicting handoffs without silently promoting partial work.

## C07 — Batch close-out and recovery

Record run/lane date, execution mode/host, question/topics/source IDs, result states, actual visual checks, coverage decision/basis, search/acquisition disposition, continuation boundary, problems/blockers, skill disposition and validation status. Registry is an index/control surface; exact claims remain in evidence records.

If context/tool/time limits interrupt a lane, persist completed locators and remaining coverage, lower/retain honest state, split or resize the lane and resume from its checkpoint. Do not repeatedly launch the same oversized job. Failure triggers a problem record and check of originals/assumptions; use [review and learning](review-learning.md) to promote only verified reusable corrections. Re-enter on new sources, changed originals, new claim scope, terminology conflict or failed citation verification.
