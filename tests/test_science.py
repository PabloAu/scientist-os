"""Synthetic mathematical fixtures, not biological or model validation."""

import json
import math
import xml.etree.ElementTree as ET

import pytest

from scientist_os.science import audit_records, meta_analysis, render_figure, summarize_csv


def test_replicate_weighting_uses_independent_units_not_frame_counts():
    # Unequal technical sampling: row weighting would give 2, but unit weighting gives 5.
    text = "group,preparation,value\nA,p1,0\nA,p1,0\nA,p1,0\nA,p1,0\nA,p2,10\n"
    result = summarize_csv(
        text, value_column="value", group_column="group", unit_column="preparation"
    )
    group = result["groups"][0]
    assert group["mean"] == 5
    assert group["n_rows"] == 5 and group["n_units"] == 2
    assert group["standard_deviation"] == pytest.approx(math.sqrt(50))
    assert group["standard_error"] == pytest.approx(5)
    duplicated = text + "A,p1,0\n" * 100
    assert summarize_csv(
        duplicated, value_column="value", group_column="group", unit_column="preparation"
    )["groups"][0]["standard_error"] == pytest.approx(5)


def test_no_declared_unit_means_no_inferential_uncertainty():
    result = summarize_csv("value\n0\n0\n0\n0\n10\n", value_column="value")
    group = result["groups"][0]
    assert group["mean"] == 2
    assert group["n_units"] is None and group["standard_error"] is None
    assert "withheld" in result["uncertainty"]


def test_missingness_is_reported_per_group_and_all_missing_units_remain_accounted():
    result = summarize_csv(
        "group,unit,value\nA,a,2\nA,a,\nA,b,\nB,c,\n",
        value_column="value",
        group_column="group",
        unit_column="unit",
    )
    assert result["rows_total"] == 4
    assert result["rows_included"] == 1 and result["rows_excluded"] == 3
    assert [item["record"] for item in result["exclusions"]] == [2, 3, 4]
    a, b = result["groups"]
    assert a["n_units_total"] == 2 and a["n_units"] == 1
    assert a["n_missing"] == 2 and a["standard_error"] is None
    assert b["mean"] is None and b["n_units"] == 0
    json.dumps(result, allow_nan=False)


def test_cross_group_units_are_rejected_even_when_one_value_is_missing():
    with pytest.raises(ValueError, match="multiple groups"):
        summarize_csv(
            "group,unit,value\nA,p1,1\nB,p1,\n",
            value_column="value",
            group_column="group",
            unit_column="unit",
        )


@pytest.mark.parametrize(
    "cell", ["NaN", "inf", "-Infinity", "1e400", "NA", "unknown", "1_000", "=1+2", "1,000", "0xFF"]
)
def test_non_numeric_nonfinite_or_ambiguous_missing_values_fail(cell):
    with pytest.raises(ValueError):
        summarize_csv(f'value\n"{cell}"\n', value_column="value")


@pytest.mark.parametrize(
    "text",
    [
        "",
        "value\n",
        "value,value\n1,2\n",
        "value,\n1,2\n",
        'value\n"1\n',
        "value\n1,2\n",
        "value\n\n",
    ],
)
def test_malformed_csv_fails_without_silent_row_skipping(text):
    with pytest.raises(ValueError):
        summarize_csv(text, value_column="value")


def test_numeric_formats_utf8_bom_and_quoted_group():
    result = summarize_csv(
        '\ufeffvalue,group,unit\n +1.2e1 ,"a,b",p1\n.5,"a,b",p2\n',
        value_column="value",
        group_column="group",
        unit_column="unit",
    )
    assert result["groups"][0]["group"] == "a,b"
    assert result["groups"][0]["mean"] == 6.25


@pytest.mark.parametrize(
    "kwargs",
    [
        {"value_column": "missing"},
        {"value_column": "value", "unit_column": "value"},
        {"value_column": "value", "group_column": "unit", "unit_column": "unit"},
    ],
)
def test_invalid_column_assumptions_fail(kwargs):
    with pytest.raises(ValueError):
        summarize_csv("value,unit\n1,p1\n", **kwargs)


def test_blank_unit_cannot_be_treated_as_a_replicate():
    with pytest.raises(ValueError, match="Independent unit"):
        summarize_csv("value,unit\n1,\n", value_column="value", unit_column="unit")


def test_csv_size_boundary_rejected():
    with pytest.raises(ValueError, match="2 MB"):
        summarize_csv("value\n" + "1\n" * 1_000_000, value_column="value")


def test_nonzero_csv_value_cannot_silently_underflow_to_zero():
    with pytest.raises(ValueError, match="underflows"):
        summarize_csv("value\n1e-999\n", value_column="value")
    assert summarize_csv("value\n0e-999\n", value_column="value")["groups"][0]["mean"] == 0


def test_fixed_inverse_variance_known_answer_and_weights():
    result = meta_analysis(
        [
            {"study_id": "a", "effect": 1, "standard_error": 1},
            {"study_id": "b", "effect": 3, "standard_error": 2},
        ],
        model="fixed",
    )
    assert result["estimate"] == pytest.approx(1.4)
    assert result["standard_error"] == pytest.approx(math.sqrt(0.8))
    assert result["Q"] == pytest.approx(0.8)
    assert result["I2"] == 0 and result["tau2"] == 0
    assert result["ci95"] == pytest.approx([-0.35304508115316313, 3.153045081153163])
    assert [s["weight_fraction"] for s in result["studies"]] == pytest.approx([0.8, 0.2])


def test_random_effects_known_answer_heterogeneity_and_model_difference():
    studies = [
        {"study_id": "a", "effect": 0, "standard_error": 1},
        {"study_id": "b", "effect": 2, "standard_error": 1},
        {"study_id": "c", "effect": 4, "standard_error": 1},
    ]
    result = meta_analysis(studies)
    assert result["estimate"] == 2
    assert result["Q"] == 8 and result["I2"] == 75
    assert result["tau2"] == pytest.approx(3)
    assert result["standard_error"] == pytest.approx(math.sqrt(4 / 3))
    assert result["ci95"] == pytest.approx([-0.2631714681523434, 4.263171468152343])
    fixed = meta_analysis(studies, model="fixed")
    assert fixed["tau2"] == 0 and fixed["tau2_dl"] == pytest.approx(3)
    assert fixed["standard_error"] < result["standard_error"]
    assert all("weight_fraction" not in row for row in studies)  # Pure function.


def test_zero_heterogeneity_and_scale_equivariance():
    studies = [
        {"study_id": "a", "effect": 4, "standard_error": 1},
        {"study_id": "b", "effect": 4, "standard_error": 2},
    ]
    result = meta_analysis(studies)
    assert result["Q"] == result["I2"] == result["tau2"] == 0
    scaled = meta_analysis(
        [
            {**row, "effect": row["effect"] * 10, "standard_error": row["standard_error"] * 10}
            for row in studies
        ]
    )
    assert scaled["estimate"] == pytest.approx(result["estimate"] * 10)
    assert scaled["standard_error"] == pytest.approx(result["standard_error"] * 10)


@pytest.mark.parametrize(
    "bad", [float("nan"), float("inf"), -float("inf"), True, "1", None, 10**400]
)
def test_invalid_meta_numeric_values_fail(bad):
    for key in ("effect", "standard_error"):
        study = {"study_id": "a", "effect": 1, "standard_error": 1, key: bad}
        with pytest.raises(ValueError):
            meta_analysis([study, {"study_id": "b", "effect": 2, "standard_error": 1}])


@pytest.mark.parametrize("se", [0, -1, 1e-200])
def test_nonpositive_or_unrepresentable_standard_error_fails(se):
    with pytest.raises(ValueError):
        meta_analysis(
            [
                {"study_id": "a", "effect": 1, "standard_error": se},
                {"study_id": "b", "effect": 2, "standard_error": 1},
            ]
        )


@pytest.mark.parametrize(
    "studies",
    [
        [],
        [{}],
        [None, {}],
        [{"study_id": "a", "effect": 1, "standard_error": 1}] * 2,
        [
            {"study_id": "a", "independence_id": "cohort", "effect": 1, "standard_error": 1},
            {"study_id": "b", "independence_id": "cohort", "effect": 2, "standard_error": 1},
        ],
        [
            {"study_id": "a", "independence_id": "b", "effect": 1, "standard_error": 1},
            {"study_id": "b", "effect": 2, "standard_error": 1},
        ],
    ],
)
def test_insufficient_malformed_or_overlapping_study_data_fails(studies):
    with pytest.raises(ValueError):
        meta_analysis(studies)


def test_extreme_numeric_scale_does_not_emit_nan_or_infinite_json():
    with pytest.raises(ValueError, match="scale"):
        meta_analysis(
            [
                {"study_id": "a", "effect": -1e100, "standard_error": 1e-100},
                {"study_id": "b", "effect": 1e100, "standard_error": 1e-100},
            ]
        )


def test_figure_escapes_labels_and_controls_and_has_no_active_content():
    result = meta_analysis(
        [
            {"study_id": '<script>alert("x")</script>', "effect": 1, "standard_error": 1},
            {"study_id": "b & c\x00", "effect": 2, "standard_error": 1},
        ]
    )
    svg = render_figure(result, title='<img src="x" onerror="alert(1)"> & title')
    root = ET.fromstring(svg)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert "&lt;script&gt;" in svg and "&amp; title" in svg
    assert not any(
        element.tag.endswith(("script", "image", "foreignObject")) for element in root.iter()
    )
    assert all(
        not any(key.lower().startswith("on") or key.endswith("href") for key in element.attrib)
        for element in root.iter()
    )
    assert "95% normal confidence intervals" in svg


def test_summary_figure_distinguishes_sem_from_ci_and_exposes_n():
    result = summarize_csv("value,unit\n0,p1\n10,p2\n", value_column="value", unit_column="unit")
    svg = render_figure(result)
    ET.fromstring(svg)
    assert "n units=2" in svg and "not a confidence interval" in svg
    no_unit = render_figure(summarize_csv("value\n1\n2\n", value_column="value"))
    assert "Uncertainty withheld" in no_unit and "n rows=2" in no_unit


def test_figure_labels_show_declared_measurement_units_and_effect_measure():
    summary = summarize_csv("value,unit\n1,a\n2,b\n", value_column="value", unit_column="unit")
    summary["measurement_units"] = "arbitrary units"
    svg = render_figure(summary)
    assert "value (arbitrary units)" in svg
    assert "measurement units unresolved" not in svg
    meta = meta_analysis(
        [
            {"study_id": "a", "effect": 1, "standard_error": 1},
            {"study_id": "b", "effect": 2, "standard_error": 1},
        ]
    )
    meta["effect_measure"] = "log risk ratio, treatment/control"
    assert "Effect: log risk ratio, treatment/control" in render_figure(meta)


@pytest.mark.parametrize("units", [None, "", "Unresolved", {"unexpected": "object"}])
def test_figure_units_fallback_is_explicit_without_fabricated_units(units):
    summary = summarize_csv("value\n1\n2\n", value_column="value")
    summary["measurement_units"] = units
    assert "measurement units unresolved" in render_figure(summary)


def test_figure_unit_and_effect_labels_are_escaped_and_bounded():
    summary = summarize_csv("value\n1\n2\n", value_column="value")
    summary["measurement_units"] = '<script>alert("units")</script> & ' + "x" * 1000
    svg = render_figure(summary)
    ET.fromstring(svg)
    assert "&lt;script&gt;" in svg and "<script>" not in svg and "x" * 100 not in svg
    meta = meta_analysis(
        [
            {"study_id": "a", "effect": 1, "standard_error": 1},
            {"study_id": "b", "effect": 2, "standard_error": 1},
        ]
    )
    assert "unresolved effect measure / units" in render_figure(meta)
    meta["effect_measure"] = "brightness < control & treatment"
    assert "brightness &lt; control &amp; treatment" in render_figure(meta)


def test_figure_rejects_missing_or_nonfinite_estimates():
    with pytest.raises(ValueError, match="nonmissing"):
        render_figure(summarize_csv('value\n""\n', value_column="value"))
    with pytest.raises(ValueError):
        render_figure({"type": "csv_summary", "groups": [{"mean": float("nan")}]})
    with pytest.raises(ValueError):
        render_figure({"type": "unknown"})


def test_figure_supports_valid_results_at_numeric_input_boundary():
    result = meta_analysis(
        [
            {"study_id": "a", "effect": 1e100, "standard_error": 1e100},
            {"study_id": "b", "effect": 1e100, "standard_error": 1e100},
        ]
    )
    ET.fromstring(render_figure(result))


def test_audit_reports_specific_provenance_and_bias_screening_without_inventing_truth():
    records = [
        {"id": "dataset-1", "kind": "dataset", "metadata": {}, "links": []},
        {
            "id": "claim-1",
            "kind": "claim",
            "content": "The treatment causes recovery.",
            "metadata": {},
            "links": [],
        },
        {"id": "software-1", "kind": "software", "metadata": {"code_commit": "main"}},
        {"id": "analysis-1", "kind": "analysis", "metadata": {"test_used_for_development": True}},
    ]
    findings = audit_records(records)
    codes = {f["code"] for f in findings}
    assert {
        "missing_authority",
        "missing_provenance",
        "missing_independence_unit",
        "missing_units",
        "missing_usage_rights",
        "unsupported_claim",
        "causal_language_review",
        "missing_immutable_software_revision",
        "test_reuse_declared",
    } <= codes
    assert all(f["message"].startswith("Screening only:") for f in findings)
    assert next(f for f in findings if f["code"] == "test_reuse_declared")["severity"] == "error"


def test_audit_does_not_treat_empty_exclusion_list_as_missing_or_short_hash_as_immutable():
    analysis = {
        "id": "an-1",
        "kind": "analysis",
        "links": ["data-1"],
        "metadata": {
            "independence_unit": "preparation",
            "units": "a.u.",
            "randomization": "not applicable: retrospective",
            "blinding": False,
            "exclusions": [],
        },
    }
    dataset = {
        "id": "data-1",
        "kind": "dataset",
        "metadata": {
            "authority": "Synthetic generator",
            "origin": "fixture",
            "license": "Apache-2.0",
            "independence_unit": "preparation",
            "units": "a.u.",
        },
    }
    software = {"id": "sw-1", "kind": "software", "metadata": {"code_commit": "a" * 40}}
    assert audit_records([analysis, dataset, software]) == []
    software["metadata"]["code_commit"] = "a" * 7
    assert audit_records([software])[0]["code"] == "missing_immutable_software_revision"


@pytest.mark.parametrize("field", ["locator", "origin_url"])
def test_visible_source_locator_fields_satisfy_provenance_screening(field):
    source = {
        "id": "source-1",
        "kind": "source",
        "content": "Checked excerpt.",
        "metadata": {
            "authority": "peer_reviewed",
            "license": "Unresolved",
            field: "Original paper, page 3, Methods",
        },
    }
    assert "missing_provenance" not in {f["code"] for f in audit_records([source])}
