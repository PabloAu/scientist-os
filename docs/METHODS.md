# Scientific methods and limits

Scientist OS beta separates deterministic calculations from model proposals and human review. The functions in `scientist_os.science` use only the Python standard library, make no model or network calls, access no files, and do not modify inputs. A successful calculation establishes that this implementation produced the reported result under its stated assumptions. It does not establish biological validity or the truth of a cited claim.

## CSV summaries: experimental units first

```python
from scientist_os.science import summarize_csv, render_figure

result = summarize_csv(
    "condition,preparation,signal\ncontrol,prep1,0\ncontrol,prep1,0\ncontrol,prep2,10\n",
    value_column="signal",
    group_column="condition",
    unit_column="preparation",
)
svg = render_figure(result, title="Synthetic signal by preparation")
```

Declare the highest relevant independent experimental unit, such as preparation or acquisition day, after inspecting the design. A cell ID is not sufficient when multiple cells share the same preparation. The function cannot infer the design from column names. Pseudoreplication arises when observations are treated as independent replication despite the experimental design; a larger number of frames does not provide more independent preparations. [Hurlbert, 1984](https://doi.org/10.2307/1942661).

For each group, the beta computes a mean within each declared unit, then gives each nonmissing unit mean equal weight. The reported sample standard deviation is the SD across those unit means; the standard error is SD divided by the square root of the number of nonmissing units. With fewer than two such units, SD and standard error are unavailable (`null`). This estimates the mean of sampled unit means, not a row-weighted mean. Units with all values missing do not contribute an estimate but remain in the accounting.

When `unit_column` is omitted, the function reports descriptive row means and sample SD only. `n_units` and `standard_error` are `null`. This avoids making an undeclared independence assumption. These summaries do not fit mixed models, weight unequal measurement precision, model time series, test treatment differences, or estimate causal effects. Repeated unit IDs within one group are intentional aggregation; the same unit in multiple groups is rejected because paired/crossover designs require a different method. An erroneous duplicate file cannot be detected from unit IDs alone.

Only empty/whitespace numeric cells count as missing. `NA`, `NaN`, infinity, malformed numbers, formula text and locale-formatted thousands separators fail the whole calculation. Convert any nonempty missing-value code explicitly and preserve that preprocessing decision. Every empty cell is returned in `exclusions` with its one-based data-record number, ending physical line, group and unit. Empty group/unit labels, ragged rows, duplicate headers, blank physical data rows, absent columns and malformed quoting are rejected. No outlier deletion, imputation or silent row skipping occurs. The CSV limit is 2,000,000 UTF-8 bytes and 50,000 data records; numeric magnitude is limited to `1e100`.

Returned fields:

| Field | Meaning |
| --- | --- |
| `type`, `schema_version`, `method` | `csv_summary`, version 1, declared aggregation method |
| `value_column`, `group_column`, `unit_column` | Exact selected header names; optional columns are `null` |
| `rows_total`, `rows_included`, `rows_excluded` | Complete accounting of parsed data records |
| `exclusions` | Explicit empty-value records; no model-generated exclusions |
| `groups[].group` | Input group label, or `All rows` when no group column is given |
| `groups[].n_rows`, `n_rows_total`, `n_missing` | Nonmissing, total and missing measurements in that group |
| `groups[].n_units`, `n_units_total` | Units with values and all observed units; both `null` without a unit declaration |
| `groups[].mean`, `standard_deviation`, `standard_error` | Unit-level estimates, or descriptive row estimates when no unit is declared |
| `groups[].unit_estimates` | Unit ID, nonmissing row count and mean; empty without a unit declaration |
| `uncertainty`, `warnings` | Method, missingness, independence and interpretation limits |

No confidence interval is computed for CSV summaries. Figure bars show **one standard error**, which is not a 95% confidence interval. Even a conventional t interval requires assumptions about independent sampling and the distribution of the unit means; the app does not verify those assumptions. [NIST, Confidence Limits for the Mean](https://itl.nist.gov/div898/handbook/eda/section3/eda352.htm).

## Generic inverse-variance meta-analysis

```python
from scientist_os.science import meta_analysis

result = meta_analysis([
    {"study_id": "synthetic-a", "effect": 0, "standard_error": 1},
    {"study_id": "synthetic-b", "effect": 2, "standard_error": 1},
    {"study_id": "synthetic-c", "effect": 4, "standard_error": 1},
], model="random")
# estimate = 2; Q = 8; I2 = 75%; tau2 = 3; pooled SE = sqrt(4/3).
```

Inputs are **human-checked study-level effect estimates and their standard errors**, not raw outcomes or prose. The caller must establish a common estimand, measurement scale, effect direction, population and comparison. For ratio measures, supply the appropriate transformed effect and matching standard error (for example log risk ratio); the beta never guesses transformations or exponentiates its output. It does not derive standard errors from p-values, extract effect sizes from articles, reconcile units, or pool incompatible designs.

For effect `y_i`, variance `v_i = SE_i²`, and `k` studies:

1. Fixed weights are `w_i = 1/v_i`; pooled fixed estimate is `sum(w_i*y_i)/sum(w_i)`.
2. Cochran's `Q = sum(w_i*(y_i - fixed_estimate)²)` and degrees of freedom are `k - 1`.
3. `C = sum(w_i) - sum(w_i²)/sum(w_i)`. The implementation evaluates the algebraically equivalent positive pairwise expression to reduce cancellation.
4. The DerSimonian-Laird between-study variance estimate is `tau2_dl = max(0, (Q - (k-1))/C)`.
5. For `model="random"`, pooling weights are `1/(v_i + tau2_dl)`. For `model="fixed"`, they remain `1/v_i` and the applied `tau2` is zero.
6. Pooled SE is `sqrt(1/sum(pooling_weights))`; the reported 95% normal interval is `estimate ± 1.959963984540054 * SE`.
7. `I2 = max(0, (Q - (k-1))/Q) * 100`, with `I2=0` when `Q=0`.

This is the classic moment-based random-effects method introduced by [DerSimonian and Laird, 1986](https://pubmed.ncbi.nlm.nih.gov/3802833/). The authors subsequently discussed limitations and refinements in [DerSimonian and Laird, 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4639420/). The beta implements the original baseline, not their later robust variance refinement.

`model` must be `fixed` or `random`. Both return the pooled estimate, pooled SE, `ci95`, `Q`, `degrees_of_freedom`, `I2` in percent, applied `tau2`, diagnostic `tau2_dl`, and study rows including their unadjusted normal `ci95` and normalized pooling `weight_fraction`. `type` is `meta_analysis`; `schema_version` is 1. Units remain those of the supplied effect scale; tau-squared has squared effect units. The fixed model still reports `tau2_dl` as a diagnostic, but does not apply it to its weights.

Supply 2–1,000 studies, unique nonempty `study_id` values, finite JSON numbers, and positive standard errors of at least `1e-100`. Strings and booleans are not numeric data. Optional `independence_id` groups reports sharing the same participants/control population; repeated IDs fail, including collision with another row's default study ID. IDs are only a declaration: differently named reports can still overlap. Shared controls, multiple outcomes and repeated follow-ups need a dependent-effects method. The input limit and finite-result checks reject unrepresentable numerical scales with a request to rescale; they do not silently cap weights.

Normal intervals ignore uncertainty in estimated heterogeneity and can be too narrow with few studies. DerSimonian-Laird is retained as a transparent baseline; REML and appropriate small-sample interval methods merit consideration for substantive synthesis. The beta does not implement REML, Hartung-Knapp adjustments, prediction intervals, meta-regression, publication-bias tests or risk-of-bias scoring. [Cochrane Handbook, Chapter 10, §§10.10.4.4–10.10.4.5](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-10).

Every result carries these limitations. A warning appears below 10 studies as a conservative **product review trigger**, not a theorem that 10 studies are sufficient. Zero estimated heterogeneity is not evidence of identical underlying effects. Neither model can repair confounding, selective reporting, incomplete searches or inappropriate eligibility criteria.

## Figures

`render_figure(result, title="...")` returns a self-contained SVG: a forest plot for meta-analysis or a grouped point summary for CSV results. The implementation validates finite estimates/bounds, escapes all labels, replaces XML-disallowed control characters, and emits no links, scripts, embedded HTML or remote resources. Up to 200 groups/studies can be plotted; all-missing groups are omitted from the drawing but retained in the numerical result. Display labels may be shortened; full study/group labels remain in point tooltips up to 300 characters. Save the numerical result with the figure.

Group figures identify the number of independent units when declared, distinguish SEM from a confidence interval, and withhold error bars when uncertainty is unavailable. Forest plots identify their normal approximation. Optional result fields `measurement_units` (CSV) and `effect_measure` (meta-analysis) appear as escaped, bounded plot labels; absent or unresolved values are explicitly labelled unresolved. These declarations do not transform data. Record physical units and transformations with the dataset/analysis. These figures are editable scientific review artifacts, not automatically publication-ready layout or evidence of scientific validity.

## Research completeness and bias screening

`audit_records(records)` emits review prompts with `severity`, `code`, `record_id` and `message`. Every message starts `Screening only:`. The rules inspect explicit record metadata and links; there is no LLM involved.

| Record/check | Metadata or evidence expected |
| --- | --- |
| Source, dataset, material provenance | `authority`; a `locator`, `origin`, `origin_url`, `source_url`, `doi`, or source link; `license` or an explicit unresolved/restricted rights statement |
| Dataset, processed data, analysis | `independence_unit` and `units`, including transformations |
| Protocol, experiment | `protocol_version` |
| Software | `code_commit` with a full 40- or 64-character hexadecimal Git object ID |
| Processed data, analysis, output | Link to data, an analysis, a protocol or software; this minimum screen does not establish complete lineage |
| Claim, manuscript | Link to evidence/claim records; human entailment review remains necessary |
| Claim language | Simple English matching of words such as `causes`, `causal` and `proves` prompts review |
| Experiment, analysis design | `randomization`, `blinding`, `exclusions`; explicit false/none/not-applicable declarations are retained |
| Test reuse | `test_used_for_development: true` triggers an error-level review prompt |
| External disclosure | `external_allowed: true` without recorded rights prompts owner review |

Unknown metadata is not filled with defaults. Empty lists of exclusions are legitimate declarations of none. A recorded license, version or independence unit is not independently verified. A lexical match may misread negation; absence of a match cannot establish lack of bias. The audit is not a formal risk-of-bias instrument, fraud detector, ethics approval, scientific validation or legal rights clearance.

## Validation evidence and next methods

`tests/test_science.py` contains hand-calculated synthetic cases for fixed/random pooling, heterogeneity, missingness, unequal technical sampling, scale transformation, absent independence, declared overlap, malformed/nonfinite data, XML safety and deterministic audit findings. These are software checks with known answers. No biological dataset, human annotation, live model accuracy benchmark or prospective scientific validation is claimed.

Higher-level hierarchical models, reproducible user-supplied analysis runners, validated PDF/table ingestion, study screening, sensitivity analysis and additional figure types should be added as separate typed tools with declared assumptions, fixtures and human review. They must not be simulated by a prompt pretending to execute an analysis.
