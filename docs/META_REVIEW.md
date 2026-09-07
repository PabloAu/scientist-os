# Controlled review and meta-analysis

Scientist OS provides a controlled review record around the existing
inverse-variance fixed and DerSimonian–Laird random-effects baseline. The
conversation leads: the host frames the question with the scientist, browses
lawfully available literature, inspects original documents/figures, records
traceable extraction and material decisions, then operates the synthesis tools.
The service never invents search results, study values or human reviews.

```python
from scientist_os.meta_review import MetaReview

reviews = MetaReview(workspace)
review = reviews.create(specification)
check = reviews.check(review["id"])
review = reviews.update(review["id"], review["revision"], patch)
review = reviews.freeze(review["id"], actual_decision,
                        expected_revision=review["revision"])
result = reviews.synthesize(review["id"])
```

The JSON host facade exposes `meta.create`, `meta.update`, `meta.check`,
`meta.freeze` and `meta.synthesize`. `create` accepts a question alone so an
empty project can begin a conversation. `check` reports missing work; it does
not pretend that incomplete research is ready for synthesis. Arrays in an
update replace the corresponding array, and expected revisions prevent
overwriting concurrent corrections.

## Review specification and decision trail

| Field | Required content before freeze |
|---|---|
| `question` | Explicit scientific question |
| `protocol` | Text declarations: eligibility, population, comparison, outcome, timing, designs, estimand, scale, direction, units, risk_of_bias_plan and model (`fixed`/`random`); predeclared `leave_one_out` boolean, optional sensitivity exclusion scenarios and `sensitivity_models` |
| `search_log` | Actual database/source, query, date (`YYYY-MM-DD`), scope, nonnegative results_count and limitations for every search |
| `studies` | All registered reports: study_id, citation/DOI, disposition, reason, decision_actor and selection_locator; included reports also declare independence_id, design, population, limitations and risk_of_bias |
| `extractions` | One chosen effect/SE per independent study, exact source record ID/revision/hash, original locator and quote, common estimand/scale/direction/units, transformation/none, verification actor/method/status and limitations |
| `comparability` | pooling_justified plus rationale, independence_assessment, population_comparison, design_comparison and bias_limitations |
| `synthetic` | True only for explicitly fictional/generated exercise material |

Keep unused and negative studies. Each report must become `included`,
`excluded` or `duplicate` with a reason; pending selection blocks pooling.
The checker detects repeated DOI or exact normalized citation identity. A
duplicate retains its own record and names `duplicate_of`; it cannot count
again. Different publications can still describe overlapping participants:
the host/scientist must investigate them and declare shared independence IDs.
Similar titles are not silently merged. Included reports require complete
extraction; excluded extractions may remain visible without being pooled.

Extraction example (IDs and values must come from inspected evidence):

```json
{
  "study_id": "registered-study-id",
  "effect": 2.0,
  "standard_error": 1.0,
  "source_id": "EXISTING_SOURCE_RECORD_ID",
  "source_revision": 1,
  "source_sha256": "EXACT_SOURCE_CONTENT_SHA256",
  "locator": "PDF p. 8, Table 2, specified row and column",
  "quote": "EXACT_REGISTERED_SOURCE_PASSAGE",
  "estimand": "The protocol's exact declared estimand",
  "scale": "The protocol's exact declared scale",
  "direction": "The protocol's exact declared direction",
  "units": "The protocol's exact declared units",
  "transformation": "Explicit transformation/formula, or none",
  "verification": {
    "status": "source_checked",
    "actor": "Actual inspecting host or scientist",
    "method": "Actual original-page/table/figure inspection performed"
  },
  "limitations": "Study-specific extraction and scientific limitations"
}
```

A located quote verifies source presence, not the interpretation or correct
derivation of an SE. The registered source content and its original-byte
attachment identity are distinct. Use the host's document/vision tools to
inspect the actual original, including figures when relevant, and record that
observation honestly. Missing or inaccessible originals need an explicit
acquisition/human handoff. Matching estimand labels does not prove scientific
comparability; the written comparison and actual human decision remain central.

## Freeze, synthesis and sensitivity

The service rejects incompatible estimands/scales/directions/units, declared
sample overlap, unverified or stale extraction, unfinished eligibility decisions,
missing search scope and unassessed pooling. It does not assume comparability
from the presence of numeric values. Freeze occurs only after these checks and
an attributed decision with actor, actor_type, kind, statement and basis.

For substantive work, `actor_type: "human"` and
`kind: "scientific_approval"` record the actual scientist's decision.
This local single-user service **does not authenticate the person**; the host
must not invent that approval. For fictional prototype exercises only,
`actor_type: "agent"`, `kind: "fixture_authorization"` is supported when
`synthetic: true`; it explicitly does not establish scientific approval.

The question, protocol, selections, extractions and comparison are hashed at
freeze. Any subsequent update reopens a draft and preserves the prior freeze
identity/history. Changed source revisions invalidate the controlled review
and its dependent outputs; repair extraction and obtain the new relevant
decision before refreezing. A preflight record is saved before calculating and
identifies the frozen review and exact calculator/service hashes and Python
version. Results are new unreviewed analyses and figures, never automatic
scientific claim approvals.

Synthesis writes:

- The exact review snapshot, result JSON, source-located extraction table and
  full selection table, including exclusions and duplicates.
- An SVG forest plot with the primary study estimates and pooled result.
- Predeclared leave-one-out influence analyses, exclusion scenarios and
  alternative fixed/random model calculations.
- Sensitivity JSON, a summary table and a separate sensitivity figure. Scenario
  estimates reuse overlapping evidence and are **never pooled together**.
- File hashes and links from review to analysis to output, so source updates
  propagate to dependent claims, text, figures and slides through normal links.

An exclusion scenario uses `name`, `exclude_study_ids` and `rationale`.
Fewer than two remaining studies is recorded as `not_estimable`; it does not
silently become a one-study meta-analysis. Up to 200 registered reports are
supported by this focused review/figure path. More complex or large reviews
can use the general recorded Python runner and an appropriately versioned
analysis module, preserving the same scientific decision contracts.

The old calculator remains a transparent baseline: independent study-level
effects and correctly derived SEs on a common scale, normal 95% intervals,
Q, I² and tau². It does not implement dependent-effects models, REML,
Hartung–Knapp intervals, prediction intervals, meta-regression, publication-bias
tests or automatic risk-of-bias scoring. Its limits and formulas are in
[Methods](METHODS.md). In particular, small-study-count heterogeneity and
normal intervals require care. Broader method choices should follow the
[Cochrane Handbook's meta-analysis guidance](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-10)
and the actual scientific design, not a default pooling button.

## Fictional worked example

`examples/pipelines/meta_fixture.py` supplies original CC0 exercise material:
three invented effects 0, 2 and 4 with SE 1, one duplicated report and one
excluded incompatible scale. All declarations and source verification are
explicitly development-agent fixture work, not human review or real literature.

The fixed/random pooled estimate is 2; Q=8, I²=75%, random tau²=3 and random
SE=`sqrt(4/3)`. Leaving out the high fictional estimate yields pooled estimate
1. The identical SEs make fixed/random pooled means coincide while uncertainty
differs. These known numbers verify software arithmetic, provenance and
failure handling. They provide no biological or literature conclusion.
