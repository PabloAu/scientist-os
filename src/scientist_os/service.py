"""Application actions shared by HTTP and CLI; models cannot invoke human review."""

import csv
import io
import json
import platform
import re
from decimal import Decimal

from . import __version__
from .science import meta_analysis, render_figure, summarize_csv
from .workspace import Workspace


def assert_current_lineage(workspace: Workspace, record: dict, seen: set | None = None) -> None:
    seen = seen if seen is not None else set()
    if record["id"] in seen:
        return
    seen.add(record["id"])
    for source_id, revision in record["metadata"].get("input_revisions", {}).items():
        if workspace.get_record(source_id)["revision"] != revision:
            raise RuntimeError("This output has stale input revisions. Recompute the analysis or regenerate its figure after review.")
    for source_id in record["links"]:
        assert_current_lineage(workspace, workspace.get_record(source_id), seen)


def create_figure(workspace: Workspace, analysis: dict) -> dict:
    if analysis["kind"] != "analysis" or "result" not in analysis["metadata"]:
        raise ValueError("Select a reproducible analysis")
    title = analysis["metadata"].get("figure_title", analysis["title"])
    svg = render_figure(analysis["metadata"]["result"], title=title)
    with workspace.transaction():
        current = workspace.get_record(analysis["id"])
        if current["revision"] != analysis["revision"]:
            raise RuntimeError("Analysis changed during figure preparation")
        assert_current_lineage(workspace, current)
        return workspace.create_record("output", f"{title} · figure", svg,
                                        metadata={"format": "svg", "figure_title": title,
                                                  "synthetic": analysis["metadata"].get("synthetic", False),
                                                  "input_revisions": {analysis["id"]: analysis["revision"]},
                                                  "external_allowed": analysis["metadata"].get("external_allowed", False)},
                                        links=[analysis["id"], *analysis["links"]])


def analyze(workspace: Workspace, spec: dict) -> dict:
    source = workspace.get_record(spec["dataset_id"])
    if source["kind"] != "dataset":
        raise ValueError("Select a registered CSV dataset")
    expected = spec.get("expected_revision")
    if expected is not None and expected != source["revision"]:
        raise RuntimeError("Dataset changed; refresh and inspect its current revision before analysis")
    method = spec.get("method", "summary")
    if method == "summary":
        result = summarize_csv(source["content"], value_column=spec.get("value_column", ""),
                               group_column=spec.get("group_column") or None,
                               unit_column=spec.get("unit_column") or None)
    elif method == "meta":
        if spec.get("comparability_confirmed") is not True or not spec.get("effect_measure", "").strip():
            raise ValueError("Confirm study comparability and specify the common effect measure first")
        reader = csv.reader(io.StringIO(source["content"].lstrip("\ufeff")), strict=True)
        studies = []
        try:
            header = next(reader, [])
            if (not header or len(set(header)) != len(header) or any(not x.strip() for x in header)
                    or not {"study_id", "effect", "standard_error"} <= set(header)):
                raise ValueError("Meta-analysis CSV needs unique headers including study_id, effect, standard_error")
            for cells in reader:
                if len(cells) != len(header):
                    raise ValueError("Meta-analysis CSV has inconsistent row widths; no cells were discarded")
                row = dict(zip(header, cells, strict=True))
                for column in ("effect", "standard_error"):
                    if not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", row[column].strip()):
                        raise ValueError(f"Each {column} must be a finite decimal value")
                    if float(row[column]) == 0 and Decimal(row[column]) != 0:
                        raise ValueError(f"{column} underflows the supported numeric range; rescale the data")
                if "independence_id" in row and not row["independence_id"].strip():
                    raise ValueError("An explicit independence_id column must be complete; no independence is inferred")
                studies.append({"study_id": row["study_id"], "effect": float(row["effect"]),
                                "standard_error": float(row["standard_error"]),
                                "independence_id": row.get("independence_id", row["study_id"])})
                if len(studies) > 1000:
                    raise ValueError("Meta-analysis supports at most 1000 studies")
        except csv.Error as exc:
            raise ValueError("Malformed meta-analysis CSV") from exc
        result = meta_analysis(studies, model=spec.get("model", "random"))
        result["effect_measure"] = spec["effect_measure"]
    else:
        raise ValueError("Unknown analysis method")
    if method == "summary":
        result["measurement_units"] = source["metadata"].get("units", "Unresolved")
    # Ensure both outputs are possible before any persistent mutation.
    render_figure(result, title=source["title"])
    metadata = {"method": method, "parameters": spec, "result": result,
                "input_revisions": {source["id"]: source["revision"]},
                "input_hashes": {source["id"]: source["sha256"]},
                "software": "scientist-os", "software_version": __version__,
                "python_version": platform.python_version(),
                "figure_title": source["title"],
                "independence_unit": (spec.get("unit_column") or "Unresolved") if method == "summary" else "study",
                "units": source["metadata"].get("units", "Unresolved"),
                "synthetic": source["metadata"].get("synthetic", False),
                "external_allowed": source["metadata"].get("external_allowed", False)}
    with workspace.transaction():
        analysis = workspace.create_record("analysis", f"{source['title']} · {method}",
                                           json.dumps(result, indent=2, ensure_ascii=False),
                                           metadata=metadata, links=[source["id"]])
        output = create_figure(workspace, analysis)
    return {"analysis": analysis, "output": output, "result": result}


def save_draft(workspace: Workspace, run_id: str, kind: str = "note", title: str = "Assistant draft") -> dict:
    if kind not in {"note", "claim", "experiment", "term", "manuscript", "decision"}:
        raise ValueError("Choose a draft record type")
    run = workspace.get_run(run_id)
    if run.get("status") != "needs_review":
        raise ValueError("Only completed proposals can be saved as drafts")
    if any(r["metadata"].get("agent_run_id") == run_id for r in workspace.list_records()):
        raise ValueError("This proposal already has a draft record; edit that record instead")
    citations = run.get("citations", [])
    content = run.get("answer", run.get("output", ""))
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False, indent=2)
    links = list(dict.fromkeys(c["record_id"] for c in citations))
    snapshots = run.get("source_snapshots", [])
    revisions = {s.get("id", s.get("record_id")): s["revision"] for s in snapshots
                 if isinstance(s, dict) and "revision" in s}
    return workspace.create_record(kind, title, content,
                                    metadata={"agent_run_id": run_id, "citations": citations,
                                              "input_revisions": revisions, "external_allowed": False,
                                              "origin": "assistant_proposal"}, links=links)


def markdown_export(workspace: Workspace) -> str:
    bundle = workspace.export_bundle()
    lines = ["# Scientist OS research handoff", "", f"Software: {__version__}", "",
             "Review status records a human decision, not independent scientific validation.", "",
             "## Records", ""]
    for record in bundle["records"]:
        lines += [f"### {record['id']} — {record['title']}", "",
                  f"Kind: {record['kind']} · Revision: {record['revision']} · Review: {record['review_status']}", "",
                  f"SHA-256: {record['sha256']}", "", "Linked records: " + ", ".join(record["links"]), "",
                  record["content"], "", "Metadata:", "", "```json",
                  json.dumps(record["metadata"], indent=2, ensure_ascii=False), "```", ""]
    lines += ["## Machine audit", "", "```json", json.dumps(bundle["integrity_manifest"]["findings"], indent=2), "```", "",
              "For the full event history, agent traces and integrity manifest, export the JSON bundle as well.", ""]
    return "\n".join(lines)
