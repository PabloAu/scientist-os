"""Bounded deterministic scientific summaries; no models, files or network access.

See docs/METHODS.md for assumptions, formulas and screening limitations.
"""

from __future__ import annotations

import csv
import html
import io
import math
import re
import statistics
from collections import defaultdict
from typing import Any

MAX_CSV_BYTES = 2_000_000
MAX_CSV_ROWS = 50_000
MAX_STUDIES = 1_000
Z95 = 1.959963984540054
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


def _number(
    value: Any, label: str, *, csv_value: bool = False, max_magnitude: float = 1e100
) -> float:
    if csv_value:
        if not isinstance(value, str) or not _NUMBER.fullmatch(value.strip()):
            raise ValueError(
                f"{label} must be a finite decimal number; only empty cells are missing."
            )
    elif isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a numeric JSON value, not a string or boolean.")
    try:
        result = float(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{label} is outside the supported numeric range.") from exc
    if not math.isfinite(result) or abs(result) > max_magnitude:
        raise ValueError(
            f"{label} must be finite with magnitude at most {max_magnitude:g}; rescale the data."
        )
    if csv_value and result == 0 and re.search(r"[1-9]", value.lower().split("e")[0]):
        raise ValueError(f"{label} underflows the supported numeric range; rescale the data.")
    return result


def _label(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 300:
        raise ValueError(f"{label} must be a nonempty string of at most 300 characters.")
    return value.strip()


def summarize_csv(
    text: str,
    *,
    value_column: str,
    group_column: str | None = None,
    unit_column: str | None = None,
) -> dict:
    """Summarize rows descriptively or equal-weight means of declared units.

    Empty numeric cells are explicitly excluded; malformed cells fail the run.
    A unit may repeat inside one group but cannot appear in multiple groups.
    Uncertainty is withheld unless an independent unit column is supplied.
    """
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_CSV_BYTES:
        raise ValueError("CSV must be UTF-8 text no larger than 2 MB.")
    requested = [value_column] + [c for c in (group_column, unit_column) if c is not None]
    if any(not isinstance(c, str) or not c for c in requested) or len(set(requested)) != len(
        requested
    ):
        raise ValueError(
            "Value, group and independent unit columns must be distinct nonempty names."
        )
    try:
        reader = csv.reader(io.StringIO(text.lstrip("\ufeff"), newline=""), strict=True)
        header = next(reader, None)
        if not header or any(not h.strip() for h in header) or len(set(header)) != len(header):
            raise ValueError("CSV needs a nonempty header with unique column names.")
        if any(c not in header for c in requested):
            raise ValueError("Requested columns are missing from the CSV header.")
        positions = {column: header.index(column) for column in requested}
        grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        group_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "missing": 0})
        unit_groups: dict[str, str] = {}
        exclusions: list[dict] = []
        rows_total = 0
        for row in reader:
            rows_total += 1
            if rows_total > MAX_CSV_ROWS:
                raise ValueError(f"CSV exceeds {MAX_CSV_ROWS} rows.")
            if len(row) != len(header):
                raise ValueError(f"CSV record {rows_total} has an inconsistent column count.")
            group = (
                _label(row[positions[group_column]], "Group label") if group_column else "All rows"
            )
            unit = (
                _label(row[positions[unit_column]], "Independent unit")
                if unit_column
                else str(rows_total)
            )
            if unit_column and unit in unit_groups and unit_groups[unit] != group:
                raise ValueError(
                    f"Independent unit {unit!r} occurs in multiple groups; use a paired or repeated-measures model."
                )
            unit_groups[unit] = group
            group_counts[group]["total"] += 1
            grouped[group][unit]  # Keep units/groups whose values are all missing in accounting.
            cell = row[positions[value_column]].strip()
            if not cell:
                exclusions.append(
                    {
                        "record": rows_total,
                        "line_end": reader.line_num,
                        "reason": "missing_value",
                        "group": group,
                        "unit": unit if unit_column else None,
                    }
                )
                group_counts[group]["missing"] += 1
                continue
            grouped[group][unit].append(_number(cell, f"CSV record {rows_total}", csv_value=True))
    except csv.Error as exc:
        raise ValueError(f"Malformed CSV: {exc}") from exc
    if not rows_total:
        raise ValueError("CSV contains no data rows.")
    warnings = [
        "Descriptive summary only; no treatment comparison, causal inference or automatic outlier removal.",
        "Measurement units are not inferred. Record units and the measurement protocol with the dataset.",
    ]
    if unit_column:
        warnings.append(
            "Independence is a user declaration, not verified. Unit means have equal weight; preserve higher-level preparation/day structure."
        )
    else:
        warnings.append(
            "No independent unit declared: means and SD describe rows; standard errors are withheld to avoid assumed independence."
        )
    if exclusions:
        warnings.append(
            "Empty value cells were excluded explicitly. Missingness may be informative; no imputation or correction was applied."
        )
    groups = []
    for group, units in grouped.items():
        unit_estimates = [
            {"unit": unit, "n_rows": len(values), "mean": statistics.fmean(values)}
            for unit, values in units.items()
            if values
        ]
        values = [entry["mean"] for entry in unit_estimates]
        n = len(values)
        sd = statistics.stdev(values) if n > 1 else None
        sem = sd / math.sqrt(n) if unit_column and sd is not None else None
        groups.append(
            {
                "group": group,
                "n_rows": sum(len(v) for v in units.values()),
                "n_rows_total": group_counts[group]["total"],
                "n_missing": group_counts[group]["missing"],
                "n_units": n if unit_column else None,
                "n_units_total": len(units) if unit_column else None,
                "mean": statistics.fmean(values) if values else None,
                "standard_deviation": sd,
                "standard_error": sem,
                "unit_estimates": unit_estimates if unit_column else [],
            }
        )
        if unit_column and n < 2:
            warnings.append(
                f"Group {group!r} has fewer than two nonmissing independent units: no uncertainty estimate."
            )
    return {
        "type": "csv_summary",
        "schema_version": 1,
        "method": "equal-weight unit means" if unit_column else "descriptive row summary",
        "value_column": value_column,
        "group_column": group_column,
        "unit_column": unit_column,
        "rows_total": rows_total,
        "rows_included": rows_total - len(exclusions),
        "rows_excluded": len(exclusions),
        "exclusions": exclusions,
        "groups": groups,
        "uncertainty": "one standard error, not a confidence interval"
        if unit_column
        else "withheld: independence not declared",
        "warnings": warnings,
    }


def meta_analysis(studies: list[dict], *, model: str = "random") -> dict:
    """Generic inverse-variance fixed or DerSimonian-Laird random-effects model.

    Input effects must share an estimand/scale and have correctly derived SEs.
    Study IDs and declared independence IDs must be unique. An ID does not
    establish independence or absence of overlapping participants.
    """
    if model not in {"fixed", "random"}:
        raise ValueError("model must be 'fixed' or 'random'.")
    if not isinstance(studies, list) or not 2 <= len(studies) <= MAX_STUDIES:
        raise ValueError(f"Provide between 2 and {MAX_STUDIES} independent studies.")
    clean: list[dict] = []
    seen_ids: set[str] = set()
    seen_units: set[str] = set()
    for row in studies:
        if not isinstance(row, dict):
            raise ValueError("Each study must be a JSON object.")
        study_id = _label(row.get("study_id"), "study_id")
        independence_id = _label(row.get("independence_id", study_id), "independence_id")
        if study_id in seen_ids or independence_id in seen_units:
            raise ValueError(
                "Duplicate study or independence ID: overlapping/dependent effects require an appropriate model."
            )
        seen_ids.add(study_id)
        seen_units.add(independence_id)
        effect = _number(row.get("effect"), "effect")
        se = _number(row.get("standard_error"), "standard_error")
        if se < 1e-100:
            raise ValueError(
                "standard_error must be positive and at least 1e-100; rescale the data."
            )
        clean.append(
            {
                "study_id": study_id,
                "independence_id": independence_id,
                "effect": effect,
                "standard_error": se,
            }
        )
    k = len(clean)
    try:
        variances = [s["standard_error"] ** 2 for s in clean]
        fixed_weights = [1 / variance for variance in variances]
        weight_sum = math.fsum(fixed_weights)
        proportions = [weight / weight_sum for weight in fixed_weights]
        fixed_mean = math.fsum(p * s["effect"] for p, s in zip(proportions, clean))
        q = math.fsum(w * (s["effect"] - fixed_mean) ** 2 for w, s in zip(fixed_weights, clean))
        # Pairwise form avoids cancellation in sum(w) - sum(w*w)/sum(w).
        c = math.fsum(
            w * math.fsum(proportions[:i] + proportions[i + 1 :])
            for i, w in enumerate(fixed_weights)
        )
        if c <= 0 or not all(math.isfinite(v) for v in (q, c, fixed_mean, weight_sum)):
            raise ValueError("Numerical scale is too extreme; rescale effects and standard errors.")
        tau2_dl = max(0.0, (q - (k - 1)) / c)
        tau2 = tau2_dl if model == "random" else 0.0
        weights = [1 / (variance + tau2) for variance in variances]
        total = math.fsum(weights)
        estimate = math.fsum((w / total) * s["effect"] for w, s in zip(weights, clean))
        standard_error = math.sqrt(1 / total)
        ci95 = [estimate - Z95 * standard_error, estimate + Z95 * standard_error]
        if not all(math.isfinite(v) for v in (tau2_dl, estimate, standard_error, *ci95)):
            raise ValueError("Numerical scale is too extreme; rescale effects and standard errors.")
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError(
            "Numerical scale is too extreme; rescale effects and standard errors."
        ) from exc
    for study, weight in zip(clean, weights):
        study["weight_fraction"] = weight / total
        study["ci95"] = [
            study["effect"] - Z95 * study["standard_error"],
            study["effect"] + Z95 * study["standard_error"],
        ]
    warnings = [
        "Human confirmation required: effects must share an estimand, scale and direction, with correctly derived standard errors.",
        "Study IDs only screen declared independence. Shared participants, controls or repeated outcomes require a dependent-effects model.",
        "95% intervals use a normal approximation; they ignore uncertainty in estimated heterogeneity and are not prediction intervals.",
        "This calculation does not assess publication bias, selective reporting, study quality or causal validity.",
    ]
    if k < 10:
        warnings.append(
            "Fewer than 10 studies: heterogeneity estimates and normal intervals can be unstable; obtain statistical review."
        )
    if model == "random":
        warnings.append(
            "DerSimonian-Laird is a transparent baseline. Consider REML and suitable small-sample interval methods for a substantive synthesis."
        )
    return {
        "type": "meta_analysis",
        "schema_version": 1,
        "model": model,
        "method": "inverse-variance fixed effect"
        if model == "fixed"
        else "DerSimonian-Laird random effects",
        "n_studies": k,
        "estimate": estimate,
        "standard_error": standard_error,
        "ci95": ci95,
        "Q": q,
        "degrees_of_freedom": k - 1,
        "I2": max(0.0, (q - (k - 1)) / q) * 100 if q else 0.0,
        "tau2": tau2,
        "tau2_dl": tau2_dl,
        "studies": clean,
        "warnings": warnings,
    }


def _xml(value: Any, limit: int = 300) -> str:
    value = str(value)[:limit]
    value = "".join(
        c
        if c in "\t\n\r"
        or 0x20 <= ord(c) <= 0xD7FF
        or 0xE000 <= ord(c) <= 0xFFFD
        or 0x10000 <= ord(c) <= 0x10FFFF
        else "\ufffd"
        for c in value
    )
    return html.escape(value, quote=True)


def render_figure(result: dict, *, title: str = "") -> str:
    """Render a self-contained SVG with escaped text and finite coordinates."""
    if not isinstance(result, dict) or not isinstance(title, str):
        raise ValueError("A deterministic result object and text title are required.")

    def declared_label(key: str, fallback: str) -> str:
        value = result.get(key)
        if (
            not isinstance(value, str)
            or not value.strip()
            or value.strip().lower() in {"unresolved", "unknown"}
        ):
            return fallback
        return value.strip()[:65]

    entries: list[tuple[str, float, float, float, str]] = []
    if result.get("type") == "meta_analysis":
        rows = result.get("studies", [])
        if not isinstance(rows, list) or not 2 <= len(rows) <= 200:
            raise ValueError(
                "Forest plots require 2 to 200 studies; select a smaller synthesis for display."
            )
        for row in rows + [
            {
                "study_id": "Pooled estimate",
                "effect": result.get("estimate"),
                "ci95": result.get("ci95"),
            }
        ]:
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("ci95"), list)
                or len(row["ci95"]) != 2
            ):
                raise ValueError("Each forest row requires an effect and a two-number ci95.")
            label = str(row.get("study_id", "Study"))
            mean, lower, upper = [
                _number(v, "Figure estimate", max_magnitude=1e102)
                for v in (row.get("effect"), *row["ci95"])
            ]
            if not lower <= mean <= upper:
                raise ValueError("Figure confidence bounds must enclose the estimate.")
            entries.append((label, mean, lower, upper, f"{mean:.4g} [{lower:.4g}, {upper:.4g}]"))
        caption = "95% normal confidence intervals; common effect scale; not prediction intervals."
        measure = declared_label("effect_measure", "unresolved effect measure / units")
        subtitle = f"Effect: {measure}; {result.get('method', 'Meta-analysis')}; k={len(rows)}."
    elif result.get("type") == "csv_summary":
        rows = result.get("groups", [])
        if not isinstance(rows, list) or not 1 <= len(rows) <= 200:
            raise ValueError("Summary figures require 1 to 200 groups.")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Summary groups must be objects.")
            if row.get("mean") is None:
                continue
            mean = _number(row.get("mean"), "Figure mean", max_magnitude=1e102)
            se = (
                _number(row["standard_error"], "Figure standard error", max_magnitude=1e102)
                if row.get("standard_error") is not None
                else None
            )
            if se is not None and se < 0:
                raise ValueError("Figure standard errors cannot be negative.")
            lower, upper = mean - (se or 0), mean + (se or 0)
            count = (
                f"n units={row['n_units']}"
                if row.get("n_units") is not None
                else f"n rows={row.get('n_rows', '?')}"
            )
            entries.append(
                (str(row.get("group", "Group")), mean, lower, upper, f"{mean:.4g}; {count}")
            )
        caption = "Bars: +/-1 standard error of independent unit means, not a confidence interval."
        units = declared_label("measurement_units", "measurement units unresolved")
        subtitle = f"{str(result.get('value_column', 'Value'))[:35]} ({units}); {result.get('method', 'CSV summary')}."
        if not result.get("unit_column"):
            caption = "Points describe rows. Uncertainty withheld because independent units were not declared."
        else:
            caption += " No bar when uncertainty is unavailable."
    else:
        raise ValueError("Unsupported deterministic result type.")
    if not entries:
        raise ValueError("There are no nonmissing estimates to plot.")
    low, high = min(row[2] for row in entries), max(row[3] for row in entries)
    padding = (high - low) * 0.08 if high != low else max(abs(low) * 0.08, 1.0)
    low, high = low - padding, high + padding
    left, right = 250, 680
    height = 190 + 34 * len(entries)

    def x(value: float) -> float:
        return left + (value - low) / (high - low) * (right - left)

    def text_at(y: int, value: str, x_pos: int = 20, size: int = 13) -> str:
        return f'<text x="{x_pos}" y="{y}" font-size="{size}">{_xml(value, 500)}</text>'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="980" height="{height}" viewBox="0 0 980 {height}" role="img" aria-labelledby="figure-title figure-description">',
        f'<title id="figure-title">{_xml(title or "Scientific summary")}</title>',
        f'<desc id="figure-description">{_xml(caption + " " + subtitle, 1000)}</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<g font-family="Arial, sans-serif" fill="#172b36">',
        text_at(32, (title or "Scientific summary")[:90], size=21),
        text_at(57, subtitle[:135], size=12),
    ]
    axis_y = 98 + 34 * len(entries)
    parts.append(f'<line x1="{left}" y1="{axis_y}" x2="{right}" y2="{axis_y}" stroke="#9aaab5"/>')
    if low <= 0 <= high:
        parts.append(
            f'<line x1="{x(0):.3f}" y1="78" x2="{x(0):.3f}" y2="{axis_y}" stroke="#bbc5cd" stroke-dasharray="4 4"/>'
        )
    for i in range(5):
        value = low + (high - low) * i / 4
        parts.append(
            f'<text x="{x(value):.3f}" y="{axis_y + 20}" text-anchor="middle" font-size="11">{value:.4g}</text>'
        )
    for i, (label, mean, lower, upper, annotation) in enumerate(entries):
        y = 95 + i * 34
        parts.extend(
            [
                text_at(y + 4, label[:31]),
                f'<line x1="{x(lower):.3f}" y1="{y}" x2="{x(upper):.3f}" y2="{y}" stroke="#176b72" stroke-width="2"/>',
                f'<circle cx="{x(mean):.3f}" cy="{y}" r="5" fill="#176b72"><title>{_xml(label)}</title></circle>',
                text_at(y + 4, annotation, x_pos=710, size=12),
            ]
        )
    parts.extend(
        [
            text_at(axis_y + 50, caption[:150], size=11),
            text_at(
                axis_y + 70,
                "Deterministic calculation; human review required. No causal or scientific validity claim.",
                size=11,
            ),
            "</g></svg>",
        ]
    )
    return "\n".join(parts)


def audit_records(records: list[dict]) -> list[dict]:
    """Screen explicit metadata for review prompts, never diagnose scientific bias."""
    if (
        not isinstance(records, list)
        or len(records) > 10_000
        or any(not isinstance(r, dict) for r in records)
    ):
        raise ValueError("Provide at most 10000 record objects.")
    by_id = {r.get("id"): r for r in records if isinstance(r.get("id"), str)}
    findings: list[dict] = []

    def flag(record: dict, code: str, message: str, severity: str = "warning") -> None:
        findings.append(
            {
                "severity": severity,
                "code": code,
                "record_id": record.get("id"),
                "message": "Screening only: " + message,
            }
        )

    for record in records:
        kind = record.get("kind")
        metadata = record.get("metadata") or {}
        if not isinstance(metadata, dict):
            flag(
                record,
                "invalid_metadata",
                "Metadata must be an object; scientific checks could not be completed.",
            )
            continue
        links = record.get("links") or []
        linked_kinds = (
            {by_id[link].get("kind") for link in links if isinstance(link, str) and link in by_id}
            if isinstance(links, list)
            else set()
        )
        if kind in {"source", "dataset", "material"}:
            if not metadata.get("authority"):
                flag(
                    record,
                    "missing_authority",
                    "Declare the source owner/authority; access alone does not establish provenance or release rights.",
                )
            if not (
                metadata.get("source_url")
                or metadata.get("origin_url")
                or metadata.get("locator")
                or metadata.get("doi")
                or metadata.get("origin")
                or "source" in linked_kinds
            ):
                flag(
                    record,
                    "missing_provenance",
                    "Record an original locator, origin, source URL/DOI or a link to the source record.",
                )
            if not metadata.get("license"):
                flag(
                    record,
                    "missing_usage_rights",
                    "Record usage rights or an explicit unknown/restricted status; no license is inferred.",
                )
        if kind in {"dataset", "processed_data", "analysis"}:
            if not metadata.get("independence_unit"):
                flag(
                    record,
                    "missing_independence_unit",
                    "Declare the experimental unit and higher-level hierarchy before interpreting uncertainty.",
                )
            if not metadata.get("units"):
                flag(
                    record,
                    "missing_units",
                    "Measurement/effect units and transformations are undeclared.",
                )
        if kind in {"protocol", "experiment"} and not metadata.get("protocol_version"):
            flag(
                record,
                "missing_protocol_version",
                "Record the exact protocol version used or proposed.",
            )
        if kind == "software":
            commit = metadata.get("code_commit")
            if not isinstance(commit, str) or not re.fullmatch(
                r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", commit
            ):
                flag(
                    record,
                    "missing_immutable_software_revision",
                    "Record a full immutable Git commit hash; a branch/tag name is insufficient.",
                )
        if kind in {"processed_data", "analysis", "output"} and not linked_kinds.intersection(
            {"dataset", "processed_data", "analysis", "software", "protocol"}
        ):
            flag(
                record,
                "missing_analysis_lineage",
                "Link the input data, analysis, protocol and/or code that produced this record.",
            )
        if kind in {"claim", "manuscript"}:
            if not linked_kinds.intersection({"source", "analysis", "output", "claim"}):
                flag(
                    record,
                    "unsupported_claim",
                    "No evidence/claim link is present; a link itself does not establish entailment.",
                )
            if re.search(
                r"\b(causes?|caused|causal(?:ly|ity)?|proves?|proven)\b",
                str(record.get("content", "")),
                re.I,
            ):
                flag(
                    record,
                    "causal_language_review",
                    "Causal/certainty language detected. Review design, confounding and evidence; this lexical rule may misread negation.",
                )
        if kind in {"experiment", "analysis"}:
            for field, code, message in (
                (
                    "randomization",
                    "randomization_undeclared",
                    "Document randomization or why it is inapplicable.",
                ),
                ("blinding", "blinding_undeclared", "Document blinding or why it is inapplicable."),
                (
                    "exclusions",
                    "exclusions_undeclared",
                    "Document exclusions, including none, and when the criteria were set.",
                ),
            ):
                if field not in metadata or metadata[field] is None or metadata[field] == "":
                    flag(record, code, message)
            if metadata.get("test_used_for_development") is True:
                flag(
                    record,
                    "test_reuse_declared",
                    "The record declares test reuse in development; do not report that test as untouched validation.",
                    "error",
                )
        if metadata.get("external_allowed") is True and not metadata.get("license"):
            flag(
                record,
                "external_disclosure_rights_unresolved",
                "External processing is allowed in metadata but usage rights are not recorded; ask the owner to resolve them.",
            )
    return findings
