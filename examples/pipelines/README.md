# Versioned execution and controlled synthesis fixtures

These are original **CC0-1.0 fictional exercise materials**. They contain no
original private research, observations, human reviews or published study data.

`summary_pipeline.py` is a normal extensible Python pipeline. Supply the full
committed revision and select `fictional_measurements.csv`. Configuration:

```json
{
  "value_column": "residual_nm",
  "group_column": "condition",
  "unit_column": "preparation",
  "units": "nm",
  "figure_title": "Fictional microscopy phantom — independent preparation means",
  "minimum_independent_units": 3
}
```

Expected uncorrected unit means: 10, 8, 6; corrected: 6, 4, 2. Group means
are 8 and 4 nm with sample SD 2 and SEM `2/sqrt(3)` nm. Ten technical observations
represent six declared independent fictional preparations. The descriptive
figure does not test a treatment effect. QC records missingness and declared
independent-unit counts. Increasing `minimum_independent_units` to 4 must produce
a retained `qc_failed` execution, useful for demonstrating failure re-entry.

`meta_fixture.create_spec(workspace)` registers three invented source excerpts
and prepares a five-report inventory: three included, one exact duplicate,
one excluded incompatible scale. A freeze for this fixture can record
`actor_type=agent, kind=fixture_authorization`, explicitly based on the user's
authorization to build fictional examples. Never invent a human scientific review.

Its random-effects baseline has pooled estimate 2, Q=8, I²=75%, tau²=3 and
SE=`sqrt(4/3)`. Fixed and random estimates coincide here because SEs are equal;
their uncertainty differs. The predeclared leave-one-out, exclusion and model
sensitivity outputs retain the study-selection and extraction trail. No claim
about literature, biology, causal effects or scientific validation follows.

See [execution manual](../../docs/EXECUTION.md) and
[controlled review manual](../../docs/META_REVIEW.md).
