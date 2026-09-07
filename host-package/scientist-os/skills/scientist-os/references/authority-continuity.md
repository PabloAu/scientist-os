# Authority, framing and continuity

## A01 — Preflight and efficient lookup

For a locator/status lookup, consult the smallest index/record that answers it. For substantive scientific work, read current context, status, roadmap, decisions and relevant open/monitoring problems, then the owning records. Split mixed questions into facets; retrieving a manuscript paragraph does not answer how the experiment was actually performed. An empty project can start from a goal with unresolved scientific facts and a pending decision queue.

Stage 0 inputs are the scientist's goal, material already supplied, roles, resources and restrictions. Record scope, smallest current question, scientific lead, collaborators, source rights/confidentiality, permitted roots/actions, intervention preference if stated, decision owners and completion criteria. Preserve unconfirmed assumptions as such. Outputs are a current project brief, roadmap, status and attributed decisions. Gate: enough scope/authority is known for the proposed action; unresolved material facts block only dependent work. Re-enter on changed aims, authority, resources, evidence or collaborator roles.

## A02 — Controlling authority by question facet

| Facet | Start from and follow to | Authority boundary |
| --- | --- | --- |
| Current status, next action, blocker | Current task/status → roadmap, decisions, problems and implicated records | Engineering completion does not close scientific gates. |
| Field science, terms, comparators, novelty | Topic/term index → source record → exact original pages and publication status | Search hits, abstract, extracted text and model prose are discovery, not read-paper verification. |
| Observation, result, interpretation | Output/panel → analysis → processed data → dataset plus material/protocol | A plot, large event count or lead recollection is not an evidence package. |
| Identity, completeness, lineage | Inventory/dataset → exact manifests, raw metadata and producer handoff | Filenames and moving derived trees do not establish identity or stable lineage. |
| Materials, conditions, actual protocol | Scoped dataset assignments → contemporaneous experimental record and confirmed versions | Generic protocol intent does not prove what happened in a particular experiment. |
| Processing and reproducibility | Processed-data/analysis record → owning software revision, run, lock and configuration | Current code, GUI screenshot, copied script or `latest` does not establish historical execution. |
| Readiness/statistical adequacy | Analysis/panel → hierarchy, exclusions, missingness, QC, alternatives and failure census | Processing-complete and visually plausible are not evidence-ready. |
| Article/caption/Methods/citation | Selected artifact → claim map, panel, verified original sources and full run lineage | Manuscript is a consumer of evidence, not authority for itself. |
| Author intent or planned experiment | Labelled proposal, presentation, notes or scientist decision | Context sources support intent/history only unless independent support is separately established. |
| Workflow transfer | Versioned procedure, contracts, problems and representative verification | Project-specific science and machine workarounds do not become general requirements. |

## A03 — Field-scoped precedence and conflicts

Internally consistent acquisition metadata controls directly encoded dimensions, channels, calibration and relative timing. It does not establish reagent identity, biological condition, purpose or clock accuracy. Contemporaneous records and explicit scoped confirmation control preparation, material/lot and deviations. Actual producer history controls what processing ran; analysis contracts control estimand and interpretation. Record field, candidate values, each source/locator, the relevant authority rule, conflict, resolution owner and disposition. Never silently resolve one class of fact using another class's authority.

For “good enough,” name the criterion: factual completeness, reproducibility, analytical validity, exact claim support, approval/readiness, or transferability. Return separate judgments when these disagree. Answer state is `confirmed`, `bounded`, `provisional`, `unresolved` or `not-represented`; attach criterion, controlling evidence, uncertainty/conflicts and the smallest discriminating next check. These states describe the answer, not universal truth or blanket source approval.

## A04 — Human decisions and hypotheses

Record a decision's exact question, options, rationale, affected records/revisions, decision-maker, date, scope, assumptions, expiry/re-entry trigger and status. Separate scientific decisions from agent implementation choices and tool authorization. Reuse a recorded answer within its literal scope; do not ask the scientist to repeat shared facts.

In the installed core, use `project.remember` with `decision_status="proposal"` for an assistant proposal. Use `recorded_human_decision` only to transcribe an actual scientist's decision, with `category="decision"`, actual `attributed_to`, exact `scope` and the relevant `source_ids`. For corpus-use approval those source IDs are required: the service binds their scientific content/metadata and upstream identities to the decision. A matching scope string without this evidence binding cannot approve another source or a changed interpretation. The service records attribution, not authenticated human identity; never invent a scientist statement to satisfy a gate. Authorized fixture calculations can record an explicitly agent/fixture decision, but cannot masquerade as a human scientific approval.

For competing hypotheses, distinguish observations from explanations and proposed tests. Compare each explanation's predictions, existing support/conflict, confounders, feasible controls and minimally discriminating experiment. Include null/negative outcomes and how each would change the decision. Planned, performed, analyzed, reviewed and externally validated are separate states. The lead supplies actual experimental facts/resources and approves material experimental commitments; the assistant may prepare designs and perform authorized analysis work.

## A05 — Living memory, steering and recovery

Keep current context/status concise, with durable decision and problem records linked to controlling evidence. Checkpoint material work with active goal, completed and pending actions, input revisions, artifacts, assumptions, human questions and next safe step. A transcript records interaction; scientific records store the durable evidential account. Update both deliberately when facts change.

A correction creates an attributed superseding decision or source revision; retain the earlier state. Inspect dependency impacts before reusing derived work. On resume, reconcile checkpoints with actual execution/output state and current revisions, re-enter the narrowest affected stage and preserve unaffected work. Do not replay completed external actions automatically. If completion is unknown, inspect evidence of the action first.

Failure handling: capture missing source, unresolved authority, contradictory values, unavailable tool or changed goal as a problem; continue independent work. Do not convert an unanswered scientific question into consent or the passage of time into approval.
