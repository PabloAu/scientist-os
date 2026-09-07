"""Controlled review state around the existing transparent meta-analysis baseline.

The capable host retrieves and inspects sources. This service preserves the
question, search and selection trail, located extraction, scientific decisions,
freeze, synthesis and sensitivity artifacts. It never searches or infers data.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import math
from pathlib import Path
import platform
import re
from uuid import uuid4

from .science import meta_analysis, render_figure
from . import __version__
from .workspace import Workspace, _bounded_json, _now, _redact


_FIELDS = {"question", "protocol", "search_log", "studies", "extractions", "comparability", "synthetic"}
_PROTOCOL_FIELDS = ("eligibility", "population", "comparison", "outcome", "timing", "designs",
                    "estimand", "scale", "direction", "units", "risk_of_bias_plan", "model")
_EXTRACTION_FIELDS = ("study_id", "effect", "standard_error", "source_id", "source_revision",
                      "source_sha256", "locator", "quote", "estimand", "scale", "direction",
                      "units", "transformation", "verification", "limitations")


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def _csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(stream.getvalue(), encoding="utf-8", newline="\n")


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _identity(study: dict) -> str:
    doi = study.get("doi", "").strip().lower()
    if doi:
        return "doi:" + re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", doi)
    # Exact normalized title/citation only. Similarity is a host review task, never silent merging.
    return "citation:" + re.sub(r"\s+", " ", study.get("citation", "").strip().casefold())


def _decision(decision: dict, *, synthetic: bool) -> dict:
    value = _bounded_json(decision, "review decision", 16_384)
    if not all(_nonempty(value.get(key)) for key in ("actor", "statement", "basis")):
        raise ValueError("Decision requires actor, statement and the source/basis of authorization")
    if value.get("actor_type") not in {"human", "agent"}:
        raise ValueError("Declare decision actor_type human or agent")
    if value["actor_type"] == "agent" and not (synthetic and value.get("kind") == "fixture_authorization"):
        raise ValueError("An agent cannot scientifically approve real study pooling")
    if value["actor_type"] == "human" and value.get("kind") != "scientific_approval":
        raise ValueError("A human freeze must explicitly record scientific_approval")
    if value != _redact(value):
        raise ValueError("Do not put credentials in scientific decisions")
    return {**value, "recorded_at": _now(),
            "authentication": "Attributed declaration; this local service does not authenticate the actor."}


class MetaReview:
    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    def _get(self, review_id: str) -> dict:
        record = self.workspace.get_record(review_id)
        if record["metadata"].get("record_type") != "meta_review":
            raise ValueError("Select a controlled meta-review record")
        return record

    def _prepare(self, spec: dict) -> dict:
        spec = _bounded_json(spec, "review specification", 180_000)
        if not isinstance(spec, dict) or set(spec) - _FIELDS:
            raise ValueError("Review fields are question, protocol, search_log, studies, extractions, comparability, synthetic")
        if not _nonempty(spec.get("question")):
            raise ValueError("Start with a review question")
        spec.setdefault("protocol", {})
        spec.setdefault("search_log", [])
        spec.setdefault("studies", [])
        spec.setdefault("extractions", [])
        spec.setdefault("comparability", {})
        spec.setdefault("synthetic", False)
        if not isinstance(spec["protocol"], dict) or not isinstance(spec["comparability"], dict):
            raise ValueError("Protocol and comparability must be JSON objects")
        if type(spec["synthetic"]) is not bool:
            raise ValueError("synthetic must be a boolean")
        for key in ("studies", "extractions", "search_log"):
            if not isinstance(spec[key], list) or len(spec[key]) > 200 or any(not isinstance(item, dict) for item in spec[key]):
                raise ValueError(f"{key} must contain at most 200 JSON objects")
        for field in _PROTOCOL_FIELDS:
            if field in spec["protocol"] and not isinstance(spec["protocol"][field], str):
                raise ValueError(f"protocol.{field} must be an explicit text declaration")
        for item in spec["studies"]:
            for key in ("study_id", "citation", "doi", "status", "duplicate_of", "independence_id"):
                if key in item and not isinstance(item[key], str):
                    raise ValueError(f"Study {key} must be text")
        for item in spec["extractions"]:
            for key in ("study_id", "source_id", "source_sha256", "locator", "quote", "estimand", "scale", "direction", "units"):
                if key in item and not isinstance(item[key], str):
                    raise ValueError(f"Extraction {key} must be text")
        if spec != _redact(spec):
            raise ValueError("Do not put credentials in review records")
        return spec

    def _links(self, spec: dict) -> tuple[list[str], dict]:
        references = {}
        for extraction in spec["extractions"]:
            if extraction.get("source_id"):
                source = self.workspace.get_record(extraction["source_id"])
                # The declared revision remains visible in extraction. The link tracks the
                # current source so draft repairs are possible after a source correction.
                references[source["id"]] = source["revision"]
        return list(references), references

    def create(self, spec: dict) -> dict:
        spec = self._prepare(spec)
        links, revisions = self._links(spec)
        return self.workspace.create_record("note", "Meta-review: " + spec["question"],
                                             json.dumps(spec, indent=2), metadata={
                                                 "record_type": "meta_review", "state": "draft",
                                                 "spec": spec, "input_revisions": revisions,
                                                 "external_allowed": False, "synthetic": spec["synthetic"]}, links=links)

    def update(self, review_id: str, expected_revision: int, patch: dict) -> dict:
        current = self._get(review_id)
        if not isinstance(patch, dict) or set(patch) - _FIELDS:
            raise ValueError("Patch replaces declared review fields; state/approval cannot be patched")
        spec = self._prepare({**current["metadata"]["spec"], **patch})
        links, revisions = self._links(spec)
        metadata = {"record_type": "meta_review", "state": "draft", "spec": spec,
                    "input_revisions": revisions, "external_allowed": False,
                    "synthetic": spec["synthetic"],
                    "reopened_from_freeze": current["metadata"].get("freeze_sha256"),
                    "reentry": "Changed protocol, evidence, search or selection requires renewed freeze."}
        return self.workspace.update_record(review_id, expected_revision=expected_revision,
                                             title="Meta-review: " + spec["question"],
                                             content=json.dumps(spec, indent=2), metadata=metadata, links=links)

    def check(self, review_id: str) -> dict:
        record = self._get(review_id)
        spec = record["metadata"]["spec"]
        protocol = spec["protocol"]
        issues, warnings = [], []

        def flag(code: str, message: str, study_id: str | None = None) -> None:
            issues.append({"code": code, "message": message, "study_id": study_id})

        for key in _PROTOCOL_FIELDS:
            if not protocol.get(key):
                flag("protocol_incomplete", "Declare protocol." + key)
        if protocol.get("model") not in {"fixed", "random"}:
            flag("model", "Select the fixed or DerSimonian-Laird random-effects baseline")
        if "leave_one_out" not in protocol or type(protocol.get("leave_one_out")) is not bool:
            flag("sensitivity_plan", "Predeclare leave_one_out as true or false")
        sensitivity = protocol.get("sensitivity", [])
        if not isinstance(sensitivity, list):
            flag("sensitivity_plan", "sensitivity must be a list of predeclared exclusion scenarios")
            sensitivity = []
        models = protocol.get("sensitivity_models", [])
        if not isinstance(models, list) or any(not isinstance(model, str) or model not in {"fixed", "random"} for model in models):
            flag("sensitivity_plan", "sensitivity_models may contain fixed and random")
        if not spec["search_log"]:
            flag("search_missing", "Record search source, query, date, scope, yields and retrieval limits")
        for search in spec["search_log"]:
            if not all(search.get(key) for key in ("database", "query", "date", "scope", "limitations")):
                flag("search_incomplete", "Each search needs database, query, date, scope and limitations")
            if type(search.get("results_count")) is not int or search["results_count"] < 0:
                flag("search_yield", "Each search needs a nonnegative integer results_count")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(search.get("date", ""))):
                flag("search_date", "Use the actual search date, YYYY-MM-DD")
        seen, identities, included = {}, {}, []
        for study in spec["studies"]:
            study_id = study.get("study_id")
            if not _nonempty(study_id) or study_id in seen:
                flag("study_identity", "Each registered report needs a unique nonempty study_id", study_id)
                continue
            seen[study_id] = study
            if not _nonempty(study.get("citation")):
                flag("citation", "Retain the report's source identity", study_id)
            status = study.get("status")
            if status not in {"included", "excluded", "duplicate"}:
                flag("selection_pending", "Every report needs an explicit selection disposition", study_id)
            if not all(_nonempty(study.get(key)) for key in ("reason", "decision_actor", "selection_locator")):
                flag("selection_trace", "Selection needs reason, decision_actor and source locator", study_id)
            identity = _identity(study)
            if identity in identities and status != "duplicate":
                flag("duplicate_report", "Duplicate DOI/exact normalized citation: retain a duplicate disposition", study_id)
            else:
                identities.setdefault(identity, study_id)
            if status == "included":
                included.append(study_id)
                for key in ("independence_id", "design", "population", "limitations", "risk_of_bias"):
                    if not study.get(key):
                        flag("study_incomplete", "Included report needs " + key, study_id)
        for study_id, study in seen.items():
            if study.get("status") == "duplicate":
                target = study.get("duplicate_of")
                if target not in seen or target == study_id or seen[target].get("status") == "duplicate":
                    flag("duplicate_target", "A duplicate must name a retained original report", study_id)
        if not 2 <= len(included) <= 200:
            flag("study_count", "Pooling/forest output needs 2–200 included independent studies")
        for scenario in sensitivity:
            if not isinstance(scenario, dict) or not scenario.get("name") or not scenario.get("rationale"):
                flag("sensitivity_plan", "Each scenario needs name, excluded study IDs and rationale")
                continue
            excluded = scenario.get("exclude_study_ids")
            if not isinstance(excluded, list) or any(not isinstance(item, str) for item in excluded) or not set(excluded) <= set(included):
                flag("sensitivity_plan", "Scenario exclusions must name included studies")
        extraction_by_study = {}
        independence = {}
        for extraction in spec["extractions"]:
            study_id = extraction.get("study_id")
            if study_id not in seen:
                flag("unknown_study", "Extraction refers to an unregistered study", study_id)
                continue
            if study_id in extraction_by_study:
                flag("multiple_effects", "One effect per independent unit is supported; choose or use a dependent-effects model", study_id)
                continue
            extraction_by_study[study_id] = extraction
            if study_id not in included:
                continue  # Retain excluded extractions but do not promote them to synthesis.
            missing = [key for key in _EXTRACTION_FIELDS if key not in extraction]
            if missing:
                flag("extraction_incomplete", "Missing extraction fields: " + ", ".join(missing), study_id)
            for key in ("estimand", "scale", "direction", "units"):
                if extraction.get(key) != protocol.get(key):
                    flag("incomparable_" + key, f"Extracted {key} does not match the declared common {key}", study_id)
            for key in ("effect", "standard_error"):
                value = extraction.get(key)
                if type(value) not in {int, float} or not math.isfinite(value) or (key == "standard_error" and value <= 0):
                    flag("numeric_extraction", "Effects and positive SEs must be finite numeric JSON values", study_id)
            if not all(_nonempty(extraction.get(key)) for key in ("locator", "quote", "transformation")):
                flag("extraction_locator", "Preserve exact source locator, quote and explicit transformation/none", study_id)
            verification = extraction.get("verification", {})
            if not isinstance(verification, dict) or verification.get("status") != "source_checked" or not verification.get("actor") or not verification.get("method"):
                flag("source_not_checked", "Host/scientist must inspect the original and record the extraction verification method", study_id)
            source_id = extraction.get("source_id")
            try:
                source = self.workspace.validate_current(source_id)
                if source["revision"] != extraction.get("source_revision") or source["sha256"] != extraction.get("source_sha256"):
                    flag("stale_extraction", "The extracted source revision/hash changed", study_id)
                quote = extraction.get("quote")
                if not isinstance(quote, str) or not quote or quote not in source["content"]:
                    flag("quote_mismatch", "Exact extraction quote must exist in the registered source", study_id)
            except (KeyError, ValueError, RuntimeError):
                flag("source_missing_or_stale", "Extraction source is missing or has stale upstream evidence", study_id)
            independence_id = seen[study_id].get("independence_id")
            if independence_id in independence:
                flag("dependent_studies", "Declared independent samples overlap; this calculator cannot pool them", study_id)
            independence[independence_id] = study_id
        for study_id in included:
            if study_id not in extraction_by_study:
                flag("extraction_missing", "Included study needs a checked located extraction", study_id)
        comparison = spec["comparability"]
        for key in ("rationale", "independence_assessment", "population_comparison", "design_comparison", "bias_limitations"):
            if not comparison.get(key):
                flag("comparability_missing", "Scientific assessment needs comparability." + key)
        if comparison.get("pooling_justified") is not True:
            flag("pooling_not_justified", "Explicitly assess whether pooling is justified; matching field names is insufficient")
        if spec["synthetic"]:
            warnings.append("Fictional fixture: this review demonstrates software only; it is not literature evidence or biological validation.")
        warnings.extend(["Search completeness, numerical extraction and semantic comparability still require scientific judgment.",
                         "Exact quotes establish source presence, not scientific support or the correctness of a derived SE.",
                         "This service does not authenticate a named reviewer, score risk of bias or infer participant overlap."])
        return {"review_id": review_id, "revision": record["revision"], "state": record["metadata"]["state"],
                "ready_to_freeze": not issues, "issues": issues, "warnings": warnings,
                "flow": {"registered": len(spec["studies"]), "included": len(included),
                         "excluded": sum(s.get("status") == "excluded" for s in spec["studies"]),
                         "duplicate": sum(s.get("status") == "duplicate" for s in spec["studies"]),
                         "pending": sum(s.get("status") not in {"included", "excluded", "duplicate"} for s in spec["studies"])}}

    def freeze(self, review_id: str, decision: dict, expected_revision: int | None = None) -> dict:
        current = self._get(review_id)
        if expected_revision is not None and expected_revision != current["revision"]:
            raise RuntimeError("Review changed; inspect the current protocol and extraction before freezing")
        check = self.check(review_id)
        if not check["ready_to_freeze"]:
            raise ValueError("Review cannot freeze: " + "; ".join(issue["message"] for issue in check["issues"]))
        spec = current["metadata"]["spec"]
        attributed = _decision(decision, synthetic=spec["synthetic"])
        metadata = {**current["metadata"], "state": "frozen", "freeze_sha256": _digest(spec),
                    "freeze_decision": attributed, "frozen_at": _now(),
                    "scientific_approval": attributed["actor_type"] == "human"}
        return self.workspace.update_record(review_id, expected_revision=current["revision"], metadata=metadata)

    def synthesize(self, review_id: str) -> dict:
        current = self._get(review_id)
        self.workspace.validate_current(review_id)
        metadata, check = current["metadata"], self.check(review_id)
        spec = metadata["spec"]
        if metadata["state"] != "frozen" or metadata.get("freeze_sha256") != _digest(spec):
            raise ValueError("Freeze the current protocol, selection and extraction before synthesis")
        if not check["ready_to_freeze"]:
            raise ValueError("Review evidence changed or checks fail; reopen, resolve and freeze again")
        included = {study["study_id"]: study for study in spec["studies"] if study["status"] == "included"}
        studies = [{"study_id": extraction["study_id"], "effect": extraction["effect"],
                    "standard_error": extraction["standard_error"],
                    "independence_id": included[extraction["study_id"]]["independence_id"]}
                   for extraction in spec["extractions"] if extraction["study_id"] in included]
        protocol = spec["protocol"]
        run_id = "run_" + uuid4().hex
        directory = self.workspace.root / "meta_reviews" / review_id / run_id
        if not directory.resolve().is_relative_to(self.workspace.root) or any(
                path.is_symlink() or path.is_junction() for path in (directory, directory.parent, directory.parent.parent)):
            raise ValueError("Meta-review output directory leaves the workspace or traverses a link")
        directory.mkdir(parents=True)
        _dump(directory / "review_snapshot.json", current)
        software = {"package": "scientist-os", "version": __version__, "python": platform.python_version(),
                    "calculator": "scientist_os.science.meta_analysis",
                    "calculator_sha256": hashlib.sha256(Path(__file__).with_name("science.py").read_bytes()).hexdigest(),
                    "review_service_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        preflight = self.workspace.save_run({"type": "controlled_meta_preflight", "status": "prepared",
                                             "execution_id": run_id, "review_id": review_id,
                                             "review_revision": current["revision"], "software": software,
                                             "freeze_sha256": metadata["freeze_sha256"],
                                             "review_snapshot_sha256": hashlib.sha256((directory / "review_snapshot.json").read_bytes()).hexdigest()})
        try:
            result = meta_analysis(studies, model=protocol["model"])
        except ValueError as exc:
            self.workspace.save_run({"id": run_id, "type": "controlled_meta_synthesis", "status": "failed",
                                     "preflight_id": preflight["id"], "error": str(exc), "software": software})
            raise
        result.update({"effect_measure": protocol["scale"] + "; " + protocol["units"],
                       "estimand": protocol["estimand"], "synthetic": spec["synthetic"]})
        result["warnings"] += check["warnings"]
        sensitivity = []
        scenarios = [{"name": scenario["name"], "exclude": scenario["exclude_study_ids"],
                      "rationale": scenario["rationale"], "model": protocol["model"]}
                     for scenario in protocol.get("sensitivity", [])]
        if protocol["leave_one_out"]:
            scenarios += [{"name": "Leave out " + study["study_id"], "exclude": [study["study_id"]],
                           "rationale": "Predeclared influence analysis", "model": protocol["model"]} for study in studies]
        scenarios += [{"name": "Alternative model: " + model, "exclude": [],
                       "rationale": "Predeclared model sensitivity", "model": model}
                      for model in protocol.get("sensitivity_models", []) if model != protocol["model"]]
        for scenario in scenarios:
            subset = [study for study in studies if study["study_id"] not in scenario["exclude"]]
            if len(subset) < 2:
                sensitivity.append({**scenario, "status": "not_estimable", "reason": "Fewer than two independent studies"})
            else:
                sensitivity.append({**scenario, "status": "computed", "result": meta_analysis(subset, model=scenario["model"])})
        _dump(directory / "result.json", result)
        _dump(directory / "sensitivity.json", sensitivity)
        (directory / "forest.svg").write_text(render_figure(result, title=spec["question"]), encoding="utf-8")
        (directory / "sensitivity.svg").write_text(_sensitivity_svg(result, sensitivity), encoding="utf-8")
        _csv(directory / "selection.csv", spec["studies"],
             ["study_id", "citation", "doi", "status", "reason", "decision_actor", "selection_locator", "duplicate_of", "independence_id", "risk_of_bias"])
        _csv(directory / "extraction.csv", spec["extractions"],
             ["study_id", "effect", "standard_error", "source_id", "source_revision", "source_sha256", "locator", "quote", "estimand", "scale", "direction", "units", "transformation"])
        rows = [{"scenario": "Primary", "model": result["model"], "n_studies": result["n_studies"],
                 "estimate": result["estimate"], "ci95_low": result["ci95"][0], "ci95_high": result["ci95"][1],
                 "I2": result["I2"], "tau2": result["tau2"], "status": "computed"}]
        for scenario in sensitivity:
            numerical = scenario.get("result", {})
            rows.append({"scenario": scenario["name"], "model": scenario["model"],
                         "n_studies": numerical.get("n_studies"), "estimate": numerical.get("estimate"),
                         "ci95_low": numerical.get("ci95", [None, None])[0],
                         "ci95_high": numerical.get("ci95", [None, None])[1],
                         "I2": numerical.get("I2"), "tau2": numerical.get("tau2"), "status": scenario["status"]})
        _csv(directory / "summary.csv", rows, list(rows[0]))
        files = {path.name: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                 for path in directory.iterdir() if path.is_file()}
        with self.workspace.transaction():
            latest = self.workspace.validate_current(review_id)
            if latest["revision"] != current["revision"]:
                raise RuntimeError("Review changed while calculating; artifacts retained but no current analysis registered")
            run = self.workspace.save_run({"id": run_id, "type": "controlled_meta_synthesis", "status": "completed",
                                          "review_id": review_id, "review_revision": current["revision"],
                                          "freeze_sha256": metadata["freeze_sha256"],
                                          "software": software, "preflight_id": preflight["id"], "files": files,
                                          "scientific_approval": False, "synthetic": spec["synthetic"]})
            analysis = self.workspace.create_record("analysis", "Synthesis: " + spec["question"],
                                                    json.dumps(result, indent=2), metadata={
                                                        "result": result, "sensitivity": sensitivity, "figure_title": spec["question"],
                                                        "meta_review_id": review_id, "execution_run_id": run["id"],
                                                        "input_revisions": {review_id: current["revision"]},
                                                        "units": protocol["units"], "independence_unit": "declared independent study sample",
                                                        "files": files, "synthetic": spec["synthetic"], "external_allowed": False}, links=[review_id])
            figure = self.workspace.create_record("output", "Forest plot: " + spec["question"],
                                                  (directory / "forest.svg").read_text(encoding="utf-8"),
                                                  metadata={"format": "svg", "figure_title": spec["question"], "input_revisions": {analysis["id"]: analysis["revision"]},
                                                            "synthetic": spec["synthetic"], "external_allowed": False}, links=[analysis["id"]])
        return {"run": run, "analysis": analysis, "figure": figure, "result": result,
                "sensitivity": sensitivity, "flow": check["flow"], "files": files}


def _sensitivity_svg(primary: dict, scenarios: list[dict]) -> str:
    rows = [("Primary", primary)] + [(scenario["name"], scenario["result"])
                                      for scenario in scenarios if scenario["status"] == "computed"]
    lo = min(result["ci95"][0] for _, result in rows)
    hi = max(result["ci95"][1] for _, result in rows)
    span = hi - lo or 1
    lo, hi = lo - span * .1, hi + span * .1
    height = 130 + 36 * len(rows)

    def x(value: float) -> float:
        return 370 + (value - lo) / (hi - lo) * 370

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="Arial,sans-serif" fill="#163340">',
             '<text x="24" y="28" font-size="19">Sensitivity of the pooled estimate</text>',
             '<text x="24" y="51" font-size="12">Overlapping evidence across scenarios; these estimates are never pooled together. 95% normal intervals.</text>']
    for index, (name, result) in enumerate(rows):
        y = 85 + 36 * index
        lower, upper = result["ci95"]
        parts += [f'<text x="24" y="{y + 4}" font-size="12">{html.escape(name[:48])}</text>',
                  f'<line x1="{x(lower):.3f}" y1="{y}" x2="{x(upper):.3f}" y2="{y}" stroke="#168a80" stroke-width="2"/>',
                  f'<circle cx="{x(result["estimate"]):.3f}" cy="{y}" r="4" fill="#163340"/>',
                  f'<text x="760" y="{y + 4}" font-size="12">{result["estimate"]:.4g} [{lower:.4g}, {upper:.4g}]; k={result["n_studies"]}</text>']
    parts += [f'<text x="24" y="{height - 15}" font-size="12">Exclusion rationales and unestimable scenarios are preserved in sensitivity.json and summary.csv.</text>', '</g></svg>']
    return "".join(parts)
