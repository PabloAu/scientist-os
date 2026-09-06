# Source audit and extraction boundary

Audit date: 6 September 2026. Source inspected: the preserved read-only `.upstream/Cell-iSCAT-Writing` clone at commit `00273003a5154672583888c6993751ad463f977e`. This report covers reusable workflow design and code structure. It contains no unpublished results, private source excerpts, raw experimental payloads or participant records.

The user requested a separate Scientist OS repository and authorized substantial redesign. The source is a private paper-development workspace with a reusable research workflow, not an existing standalone Scientist OS application. The new beta implements a generic product boundary in Python. The preserved clone, its Git history, project-specific records and adjacent scientific applications are excluded from the new product's release files.

## What the source contributes

The source README presents a dual purpose: writing a scientific paper and developing reusable evidence-controlled research mechanics. `PROJECT_PLAN.md` defines the complete lifecycle from project configuration and dataset inventory through provenance, literature, analysis, manuscript drafting, review, release and post-submission revision. `PROVENANCE.md` provides the material/protocol/data/analysis/output chain and requires exact software revisions. `corpus/WORKFLOW.md` distinguishes registration, extraction, mapping, verification and approval. `SOFTWARE_ANALYSIS_WORKFLOW.md` separates application ownership from paper-specific configuration and interpretation.

These are valuable design requirements. They are distinct from evidence that every stage was enforced by a reusable runtime. Source registration does not prove a scientific claim; visual inspection is not equivalent to text extraction; approved wording is not universal approval of a source. The beta preserves those distinctions in its documented limits and human review model.

## Findings confirmed by source inspection

| Finding | Source evidence | Beta response and remaining limit |
| --- | --- | --- |
| Product boundary mixed with private research | Root README, project-specific registries and source tree; `pyproject.toml` describes the writing workspace | New package and synthetic examples; original clone/history stay outside distribution. Generic workflow ideas are reimplemented, not copied wholesale with private records. |
| Coordinator prepares packets but does not run a self-contained agent | `.codex/skills/orchestrate-corpus-ingestion/scripts/orchestrate_ingestion.py`, `prepare`, `validate_handoffs` and CLI dispatch | New bounded provider-neutral tool loop; no claim that the old helper executed models or enforced operating-system permissions. |
| Packet path uses an insufficiently restricted lane ID | `validate_plan` accepts nonempty unique `lane_id`; `prepare` interpolates it into `packets_dir / f"{lane_id}.json"` | Do not reuse this writer. New agent actions address existing record IDs through an allowlist and never receive arbitrary file-write tools. The original helper remains unchanged. |
| Handoff validation trusts supplied attestations | `validate_source_result` compares provided before/after hashes to a manifest; `validate_handoff` accepts an asserted empty write list; visual verification requires a supplied locator list | New runtime checks exact quotes and current registered-source content hashes. Those checks establish identity and excerpt integrity, not entailment, true page viewing, or enforcement against a privileged external actor. |
| Workflow is specialized to one research project | Coordinator topic constants, mandatory reads, source-folder assumptions and structural audit requirements | Generic typed records and user-selected context/style replace fixed project taxonomies. Scientific unit/authority choices remain user declarations. |
| Structural completeness can be mistaken for scientific readiness | `.codex/skills/audit-paper-workflow/scripts/audit_project_structure.py` checks files, registries, headings and consistency; corpus workflow separately requires scientific review | New completeness rules are explicitly called screening. Deterministic calculations have numeric fixtures; human approval is recorded separately from implemented/evaluated/validated claims. |
| Starter onboarding and restore verification were still pending in source records | `memory/STATUS.md` and reusable-template work in `PROJECT_PLAN.md` | New beta packaging, manual, examples and local UI provide onboarding. Release verification must report only checks actually run; a backup/export is not an independent recovery certification. |
| Instructions carried much of the safety/quality policy | Source skills and prose define read-only lanes, coordinator ownership, external-model restrictions and review gates | Runtime restrictions and persistent events support those policies. The beta remains a single-user local app, not an isolation sandbox or multi-user authorization service. |

Two findings were reproduced using a **copied helper in a disposable fixture directory**, with no scientific sources or source-workspace execution. The helper's SHA-256 before and after the audit was `bc7ef05ad7fb4ae9d402200542309cfc1189fa8f2f3dec071dd90265bb33da33`.

1. A minimal synthetic manifest and dummy mandatory-read files satisfied `validate_plan`. The lane ID `../../escaped` passed validation. `prepare` returned zero and created `escaped.json` above its run/packet directory, still contained in the disposable fixture root. This confirms the output-containment defect rather than merely inferring it.
2. A synthetic result with matching manifest/attested hashes, a supplied `page 900` locator and `proposed_state="verified"` passed `validate_source_result` without any corresponding scientific source or viewed page. This demonstrates that the validator checks declarations, not their truth; it is not a claim that the original authors fabricated a handoff.

The fixture was removed after its assertions passed. No original helper or research record was changed, and the original helper hash remained identical. No model requests, scientific analyses or training jobs were run. The source checkout's tracked working tree was clean during inspection.

## Lifecycle extraction coverage

| Scientific need | Concrete beta surface | What remains human-led or outside this beta |
| --- | --- | --- |
| Register data, materials and protocols | Typed records, explicit metadata, linked provenance and revision review | Confirm acquisition facts, rights, material identity, true independence and protocol applicability |
| Track data transformations and code | Processed-data, analysis, output and software records; exact version metadata; deterministic outputs | Execute arbitrary scientific code, capture external instrument data or verify remote repository state |
| Answer questions and audit work | Selected-record retrieval, exact quote/hash checks, bounded model proposals, deterministic completeness screening | Assess entailment, experiment validity, confounding and substantive bias |
| Suggest experiments | Evidence-bounded experiment proposal task and editable experiment/decision records | Choose design and resources; authorize and conduct experiments |
| Meta-analysis | Explicit study effects/SEs, fixed and DerSimonian-Laird calculations, forest SVGs | Systematic search/screening, extraction validation, compatible estimands, dependency modelling and advanced inference |
| Terminology and writing | Term/manuscript records; terminology, manuscript and journal proposal tasks with selectable sources/style | Final scientific language, authorship, current journal requirements and submission decisions |
| Make figures | Deterministic CSV group summaries and meta-analysis forests | Microscopy/image pipelines, arbitrary plotting scripts, multi-panel journal layout and image integrity inspection |
| Human direction throughout | Source selection, task/style guidance, editable records, named review decisions and traceable runs | Human scientific judgement; model proposals are never scientific approval |
| Evolve across models | Provider adapter and bounded tool interface; integration documentation | Proving arbitrary provider compatibility, evaluating scientific task quality, paid service commitments |
| Post-submission revision | Reusable records can track reviewer requests, evidence and decisions | Dedicated editor-letter import, response matrix, tracked Word changes and automated resubmission packaging |

The source's six ingestion states are not all reproduced as independent automatic transitions. The beta's record review states are a smaller product contract; text ingestion, semantic verification and approval must not be conflated. This is an explicit scope boundary, not a claim of full source feature parity.

## Evidence and release discipline

The audit read the preserved clone's README, provenance model, lifecycle sections, corpus workflow, coordinator validation/preparation code, structural checker, software ownership workflow and current status. It also reconciled the earlier portfolio audit against the same source commit. It did not inspect every historical revision or validate unpublished scientific conclusions. No third-party paper content, imported research data, existing project-specific examples or private software payloads were selected for the product.

The generic harness is newly implemented under the product's chosen license; that license does not relicense material held in the preserved source clone or any future imported research. Keep source-specific usage rights in the records and review the exact release file inventory. A private clone inside the local project is a provenance reference, not part of the installable package or a publication decision.
