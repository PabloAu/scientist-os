# Experiment inventory and provenance

## I01 — Lead-first inventory and complete queues

Stage 1 begins with the complete supplied experiment/source inventory, including unused, negative, incomplete, deferred and excluded candidates. Reconcile an index/workbook with detail sheets, existing records and result families before assigning identities. Preserve original row/date/path labels, ordering and unresolved mismatches. A permitted mixed-document folder can be scouted without assuming that an undescribed experimental dataset is available for analysis or release.

Before accessing a new raw experimental candidate, reuse its existing owner description if adequate. Otherwise obtain the owner's general account of the experiment/data, purposes and outcomes. Existing explicit owner description and authorized scope satisfy this gate; avoid a repeated checklist or permission question. Until resolved, keep the candidate in the review queue and continue documentary or other independent work. If excluded before registration, retain its inventory/disposition but do not open raw storage or allocate a dataset record; preserve a historical dataset identity if one already exists. Retained candidates receive stable identities. Dataset cards remain linked to review/active/deferred/closed queues and source index rows.

## I02 — Raw scope and acquisition census

Resolve exact selected roots; a stale path's candidate replacements remain unresolved until supported. Snapshot scope, date, file/byte counts, zero-byte files, extensions, structure, time range, inaccessible items and raw/derived classification. Inventory raw acquisition independently of moving derived branches. Manifest entries resolve relative to their manifest's directory and remain within permitted roots. Record an explicit provisional large-file hash state when hashing is deferred; it is not a checksum or immutable lineage.

Use a pinned, declared modality adapter for metadata; record version, file-level success/error/warning and the fields it actually measures. Retain raw errors and the denominator of all intended acquisitions, including failures. Do not derive frame count from bytes, replicate identity from names, or acquisition chronology from copy-sensitive timestamps. Compare embedded absolute time with file chronology when copy/export sensitivity matters; retain relative timing and uncertainty separately. Reduce reader concurrency after contention/memory errors; avoid repeated scans of unchanged or actively written trees.

Record conditions, groups, controls, independent/experimental units and nesting, completeness, exclusions, usability and potential use. Label filename-derived interpretations as inferred. A generic adapter contract replaces instrument-specific paths/readers; unsupported modalities remain explicitly uninspected.

## I03 — Full provenance cards and scoped assignments

Preserve dataset → materials/protocols → processed data → analysis → output → claim/artifact navigation. Store upstream dependencies; derive downstream usage views instead of inserting dependency cycles. Each card identifies exact original location/version/hash, producer or decision owner, authority, confidentiality/rights, current state, relevant dates, limitations and linked records.

Materials specify identity/lot/preparation and provenance. Protocols specify version, intended procedure and evidence of actual applicability. A dataset assignment records literal branch/file/group/time scope, record and historical version, local deviations, evidence/precedence and confirmed/unresolved status. Ask once about a reusable detail after searching shared records; store it in the narrowest shared record. Do not apply an answer to other scopes by inference. Retain one-off deviations on the dataset; create reusable variants only when scientifically distinct and recurrent.

Processed-data cards specify producer, exact raw inputs, transformations, stage order, code/config/environment, units/calibration, exclusions, QC and output roots/manifests. Analysis cards additionally declare question/estimand, independent units/nesting, assumptions, uncertainty, alternatives, failure denominators and permitted downstream use. Outputs identify their exact analysis/run, bytes/hash, panel role, caption facts and review state.

## I04 — Stable producer handoff

Separate completed raw inventory from incomplete derived provenance. If processing is active, record exact intended output roots and observed status, set `processing-active` and stop the derived pass. Resume when producer/lead confirms completion for inventory and supplies root, software/environment/configuration, intended outputs and known exclusions.

Take two read-only manifests of those roots separated by a recorded interval appropriate to the producer. Require unchanged file count, bytes and latest modification time, and compare individual identities/hashes for relied-upon files. Record both observations. If changed, return to `processing-active`; a stable interval alone does not prove producer completion or scientific correctness.

Reconcile physical parameters across every processing stage: calibration, timing, coordinate units, rescaling and selection thresholds. Mismatch that could alter selection/scaling is a material conflict, not automatically corrected by the final table. Inspect literal table headers before case-insensitive parsing; preserve case-distinct columns with explicit names, counts and actual producer usage. Use a manifest's intended acquisitions/outputs as the denominator; broad filename globs may include aggregate/subset files. Missing legacy manifests leave completeness unresolved rather than proving failure.

## I05 — Six dataset readiness states

| State | Entry evidence and next gate |
| --- | --- |
| `raw-inventory-active` | Raw discovery/metadata reconciliation is incomplete. Complete scope, census, errors and conflicts first. |
| `provenance-pending` | Raw inventory complete; identity, conditions, control, unit or processing facts still unresolved. Resolve owning facts. |
| `processing-active` | Derived outputs changing or producer handoff missing. Require I04 before stable lineage. |
| `analysis-ready` | Stable lineage, explicit question, inputs, units, exclusions and validation plan. Run the approved/frozen analysis. |
| `evidence-ready` | Analysis and output evidence package passes required QC for a bounded candidate use. Scientific-use approval remains scoped. |
| `closed-excluded` | Attributed lead exclusion, reason and downstream consequences preserved. Re-entry requires a new decision. |

These states are distinct from record `unreviewed/approved/rejected`. A dataset can be raw-complete without any processed outputs; it cannot be called evidence-ready because it looks promising. Transition records name evidence, reviewer/decision owner, affected version, missing gates and permissible use.

## I06 — Audit, invalidation and re-entry

At preflight reconcile queues/cards, raw scope, result-family continuity, producer state and open problems. At close-out reconcile index/detail rows, identities, counts, shared assignments, downstream uses, unresolved questions and readiness. Optional enrichment cannot silently expand raw scope. Persist failures and consolidated questions with recognizable experiment/date/locator labels.

New or changed dataset, material/protocol applicability, source interpretation or analysis input reopens affected states and derived dependencies. Compare old/new hashes and revisions; mark affected results, claims, manuscript passages and slides stale. Preserve exact earlier outputs/runs and reconcile undeclared dependencies explicitly. A software invalidator only catches declared links. Recompute/review through the owning stage; never silently rebase quotations or approve changed evidence.

In the installed core, changed-byte incorporation advances the stable source/dataset identity and reports transitive affected IDs. `ingest.reextract` also changes the interpretation revision and resets corpus-use state while keeping the exact original bytes. Treat both as possible downstream invalidation events. `science.record` / `science.reconcile` preserve planned versus owner-described actual facts; their planned/performed/analyzed/validated status is a different axis from these six dataset-readiness states. The full inventory-readiness gates remain a supplied scientific procedure and must not be inferred from a generic `performed` status.
