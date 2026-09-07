# Narrative, software, Python analyses and panels

## P01 — Stage 2: smallest defensible contribution

Use the question, complete inventory, governed results, verified literature and constraints to choose a coherent contribution. Separate essential results from optional exploration. Compare alternative narrative spines; identify what evidence would overturn each. The scientist approves central claims/spine and material scope changes. Outputs are a claim map and panel contracts, not a promise that each panel will succeed. Missing evidence, contradictory results, cut panels or changed objectives reopen this stage.

A panel contract specifies role/question, exact inputs, analysis/estimand, display, intended observation, alternative explanations, controls, permissible/prohibited claims, limits, independent units/nesting, missingness/exclusions/failures, sensitivity/falsification, caption facts, dependencies, owner and cut criteria. States: `idea`, `mapped`, `analysis-ready`, `review-ready`, `approved`, `cut`. Approval records exact version and bounded use; cutting preserves evidence and rationale. Do not promote merely because the panel was placed in a storyboard.

## P02 — Stage 3: software ownership and immutable production identity

Reusable scientific methods belong in accessible owning software repositories; project-specific orchestration/config stays with the project. Inspect and modify code in its owning checkout, not a copied private source. Record repository URL, exact immutable commit, branch only as navigation, clean/dirty status and patch hash. Keep raw/source records untouched. Local exploratory work may use an explicitly dirty revision; production evidence requires the frozen committed code and resolved configuration.

When a GitHub-backed production run is relied upon, verify the exact commit is available at the recorded remote (within source rights/authorization); a branch name or local commit does not establish remote availability. If push/distribution is pending, label it `local-only / remote-unverified` and do not claim the handoff is externally replayable. Do not publish private data or software to satisfy this gate. Record any restriction and safe access path.

Pin runtime/dependencies with lock/environment identity and hash; record configuration bytes/hash, resolved defaults, seeds, method/module/entry point, execution command, units/physical parameters and platform details relevant to replay. When migrating legacy/current software, choose representative cases before inspecting acceptance results; compare numerical and visual outputs against declared tolerances and adjudicate discrepancies. Fix the owning code/docs, not a downstream figure to hide disagreement. Reconcile software user docs, Methods and configuration after changes.

## P03 — Stage 5: exploration, freeze and execution

First inspect the selected permitted dataset/schema/units and hierarchy. Record candidate observables/displays, scientific estimand and competing analyses, measurement semantics, candidate failures, baseline methods and why the chosen variable is fit for purpose. State which choices were informed by data. Freeze hypotheses, splits, exclusions, estimand, units, statistical method, metrics/tolerances and planned sensitivity before test/confirmatory inspection. The lead decides material scientific choices. Do not relabel a data-informed endpoint as prespecified.

Execute extensible Python tools, developing/versioning a suitable module where required. A menu of built-in calculators is not a limit on the host; use them only when their assumptions fit. Preserve biological/experimental/statistical hierarchy, pairing/time dependence and missingness. Split at the independent acquisition/sample/preparation/day when appropriate; never let related frames/crops cross evaluation boundaries. Do not equate observation count with independent replication. Compare appropriate physical/classical baselines before adding complexity. No paid compute is assumed; use a smoke run before substantial local compute and avoid overlapping GPU jobs.

Freeze selected input identities/hashes and declared selection/exclusion criteria. The run record contains purpose/hypothesis/estimand, plan/decision references, inputs/versions/locators, software/repository/commit/dirty patch, environment/lock, command/config/resolved parameters/seeds, time/status/logs, units/hierarchy, QC/exclusions/missingness/sensitivity, limitations, output hashes and downstream record links. Record failed runs and the full intended denominator, including failed/excluded acquisitions. Never silently drop nonfinite/malformed values or substitute a successful subset for all attempted work.

For simulations/fictional fixtures, explicitly set the run specification's `synthetic=true` in addition to the scientific plan/result labels. Do not rely on the pipeline's text to set run metadata. A host setup mistake belongs in an attributed correction while immutable run bytes remain unchanged. Missingness among present table rows does not count planned-but-absent acquisitions; retain that denominator from the authoritative experimental record separately.

`analysis.run` executes the selected committed snapshot, preserving dirty/patch information without silently executing working-tree changes. Verify and replay through `analysis.verify` / `analysis.replay`. The runner records current environment and cached remote information; it does not recreate dependencies or verify live remote availability. Treat a successful local replay as that precise result.

For a supported numeric figure payload, use `analysis.register_result(run_id, result_file, figure_title)` after verification. Select the exact JSON output filename recorded in the run. The operation requires an intact completed Python run with current sources, verifies that selected output's location/hash, validates supported result/figure semantics and creates linked analysis/output records. Preserve the exact figure-title binding through export. This is a bridge for the renderer's supported result schemas, not an automatic adapter for arbitrary pipeline outputs. For other outputs, use a deliberate adapter and the same lineage/visual review contract; do not forge native result metadata to bypass validation.

## P04 — Evidence-package gate

A quantitative panel becomes review-ready only when all nine checks have evidence:

1. Complete dataset/material/protocol/processed-data/analysis/output linkage.
2. Exact immutable inputs and stable producer lineage.
3. Versioned executable software and declared environment.
4. Frozen statistical unit, exclusions, estimand and measurement meaning.
5. QC, missingness, uncertainty and relevant sensitivity/falsification, including failure denominators.
6. Numerical replay against declared equality/tolerances and actual visual regeneration inspection.
7. Caption facts and explicit permitted/prohibited claims.
8. Verified original sources/locators and reviewed terms for literature-dependent statements.
9. Attributed scientific-lead approval of the bounded panel use before approved promotion.

Run appropriate independent QC: schema/value/unit checks, expected invariants, representative raw-to-output trace, baseline/alternative comparison and failure review. Independence of the check refers to an independently executed check/reader when supplied, not a second label attached to the original result. State checks not performed. Synthetic recovery validates only the declared generator; it is not biological or external validation.

## P05 — Failure, replay and re-entry

If lineage/configuration is missing, pause production and continue exploratory work with that limit labelled. If calculations fail, preserve input/run/logs and exact failure; do not promote. If software replay or visual parity diverges, record discrepancy, investigate the owning stage and obtain material scientific decisions before changing acceptance tolerances. Never tune a confirmatory threshold after test inspection without declaring the revision exploratory and creating a new plan.

Re-entry triggers include new data, changed protocol/material applicability, unit/selection corrections, code/environment/config changes, QC failures and narrative changes. Mark dependent panels/claims/artifacts stale, retain old runs and re-run only affected work. The reproducibility claim is about recorded calculation and declared tolerances. Model wording can vary; record host/model identity and decision/tool observations without promising deterministic prose.
