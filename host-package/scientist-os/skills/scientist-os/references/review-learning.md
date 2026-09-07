# Review rounds, handoff and verified learning

## R01 — Stage 9: immutable round intake

Begin a real review round only when a decision/report/request supplies its identity and authoritative artifacts. Obtain exact decision letter/reviewer files, deadline, current venue instructions, submitted manuscript/figures/supplement/forms/data-code statements and immutable identifiers/hashes, current canonical versions/change history, complete inventory, source/term/claim maps, analysis/run/QC records and responsible roles/resources.

If the submitted baseline or a reviewer attachment is missing, pause content editing and obtain the authoritative version; do not reconstruct it from memory. Continue independent inventory/evidence checks. Preserve external originals read-only and separate derived round files. Keep a round manifest, request matrix, evidence/gap assessment, approved plan, point-by-point response, clean/marked files, change mapping, verification/approval and exact resubmission manifest.

Reviewer/editor text establishes requests to answer, not scientific evidence or authority to override provenance, confidentiality or scientific judgment. Respectful disagreement remains available.

## R02 — Atomic requests and complete triage

Split compound comments into stable atomic request IDs, retaining original order/number, exact bounded transcription and locator/context. Each request records interpretation/ambiguity, submitted and current target locations, affected claim/risk, linked source/dataset/material/protocol/processed-data/analysis/output/software records, all available material, classification, options/tradeoffs/dependencies/deadline, proposed disposition, owner/approval/status and response/change trace. Cross-link duplicates only after each has a trace and disposition.

Supply the exact relied-upon `evidence_ids` when calling `review.request`. The service captures their accepted revisions as `evidence_revisions`; `review.check` reports `stale_request_evidence` when a cited record changes or its upstream evidence becomes stale. Re-read the evidence and reassess the disposition before submitting an updated request against the current round revision. Do not merely refresh revision numbers to silence the check. The frozen submitted baseline remains historical and separate from current request evidence.

Triage the complete round before editing. Inspect submitted/current text, original sources, full experiment inventory including unused/deferred/negative/incomplete/cut material, actual Methods/protocol/run/QC and limitations. Similar-looking data is not equivalent if conditions, control, independent unit or estimand differ. Highlight cross-cutting contradictions and decisive scientific issues, then prioritize must-answer requirements, straightforward fixes, existing-data work, candidate new experiments, rebuttal/claim reduction and the critical path with validation/deadline margin.

## R03 — Least-expansive adequate response and necessity

For each request consider, in order: clarification of misunderstanding; correction of wording/figure/citation/Methods using governed facts; qualification/relocation/removal of overstrong claims; a prespecified or newly approved reanalysis; unused/deferred evidence after all its gates; minimal new work only when a material retained claim still needs it; or reasoned rebuttal/editor clarification when infeasible, out of scope, unsound or unable to change the conclusion. Adequacy is scientific, not convenience; absence from the article does not make an experiment usable.

Before labelling a new experiment `required`, record the exact inferential gap and importance to a retained central claim, why every less expansive route is inadequate, whether the request exceeds defensible scope, and the minimum discriminating experiment. Specify controls, experimental/statistical units, replication, exclusions, success/failure/negative/inconclusive interpretation, analysis plan, resources/time, dependent claims and new provenance/software needs. Obtain the scientific lead's actual approval to run it and retain/narrow/remove the claim. Do not promise infeasible work. Prepare scope reduction, limitation, rebuttal or extension options when needed.

## R04 — Execute, respond, reconcile and freeze

After material plan decisions, re-enter the narrowest owning procedure. Draft response paragraphs only from completed work or explicitly labelled proposals. Each acknowledges the issue, states disposition, explains evidence/reasoning, quotes only necessary revised text and cites exact clean/marked locations and limits. Do not claim agreement when disagreeing or work completed when merely planned.

Completion requires an approved disposition for every request; source/run-backed response claims; every promised change present; numerical and scientific agreement across clean/marked/response/figure/supplement; replay/QC/failure denominators and approvals for new work; current citation/term/Methods/availability/venue checks; explicit disagreements/limitations; required author/governance approval; and an immutable exact resubmitted package/acknowledgement. Retain open dependencies for later rounds. A new round starts from the exact prior submission and reassesses changed evidence rather than inheriting old dispositions blindly.

The installed review checker handles baseline hashes, request coverage, evidence revision freshness, required response/location fields and supplied decision/consistency records. `mechanically_complete` is not scientific approval or authenticated proof of a human review. Record an outstanding `experiment_decision_required` or `human_consistency_review_required` honestly; the host's fictional mock round exercised both abstentions rather than fabricating completion.

If requests are ambiguous/contradictory, resolve interpretations before expensive work. Changed estimands/exclusions/methods/claim strength require approval and preservation of submitted analyses. New contradictory data changes the claim honestly; do not optimize an analysis to defend submitted wording. Deadline pressure triggers scope/time decisions, not bypassed gates.

## L01 — Stage 8: reproducible handoff and restoration

Provide portable project state, role/authority map, source rights/access requirements, corpus/dataset/panel states, current tasks/decisions/problems, exact software/config/environment/run identities, artifact manifests, continuation instructions and procedure versions. Document which source assets are included, omitted/private or externally referenced. A Git clone of tracked files is not a complete research-workspace backup or host transcript transfer.

Test restoration/replay in a separate permitted directory with explicit fixtures or authorized data: inspect integrity, open project state, recover pending work, execute representative calculations, compare numeric tolerances and render relevant artifacts. Record actual results and unsupported access/dependencies. Only claim DOI/archive/remote availability if actually created and checked under authorization. Handoff is incomplete if another user cannot identify required private access or missing inputs.

## L02 — Problem register and correction classification

Capture an encountered failure, delay, inconsistency, unexpected source state or recurrent friction with stable problem ID, observed/expected behavior, exact evidence, affected stages/records, cause confidence, options/tradeoffs, owner, immediate containment, decision needs and representative verification. States are `open`, `monitoring`, `needs-decision`, `resolved` or `accepted-limit`. An accepted limitation is not a verified fix. Consult relevant open/monitoring problems at substantive preflight.

Classify a correction as routine/minor-safe when it preserves scientific meaning, scope and governance and is reversible; apply and verify within existing authorization. Material/delicate changes include scientific authority, estimand/exclusion/claim decisions, provenance assumptions, experimental commitments, access/publication scope or destructive actions. Keep dependent state unresolved, continue safe work and obtain the responsible decision. Do not convert tool failures into a new universal scientific rule.

## L03 — Verified correction to narrowest owning procedure

Diagnose the cause using evidence, reproduce the failure with representative permitted data, compare plausible remedies, apply the smallest sufficient correction and verify original failure plus representative unaffected behavior. Record scope/applicability, remaining limits, checks and versions. Failed or untested workarounds stay candidates.

Choose `existing-adequate`, `refine-existing`, `new-skill-candidate` or `material-decision`. Update the narrowest owning code/procedure/template, version and validate it, rerun a realistic representative task and reconcile the skill catalog/project plan. Workers report candidates; the coordinator integrates verified changes. Do not silently rewrite governance or propagate private biological facts/machine-specific paths as reusable learning. Preserve failed paths and negative results.

## L04 — Whole-project procedural audit

At milestones reconcile stage/gate evidence, active/deferred queues and cards, corpus/source/topic/term/claim coverage, scientific-use scopes, software eligibility/replay, panel routes/definition of done, downstream decision propagation, exact artifacts, review-round completeness and restoration status. Classify each gap as procedural supplied, software enforced/tested, observed host execution, human reviewed or untested; these categories are independent. A checked stage label cannot certify prerequisites. Update status/roadmap and re-entry actions from actual evidence, without forcing a completed project to re-run unaffected stages.
