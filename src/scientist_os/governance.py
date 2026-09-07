"""Review, panel and workflow-improvement records beneath a capable host.

Mechanical completeness is not scientific approval. Decision statements are
attributed, not authenticated, in this single-user local prototype.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .workspace import Workspace


def _required(value: dict, keys: tuple[str, ...]) -> None:
    if not isinstance(value, dict):
        raise ValueError("Expected an object")
    missing = [key for key in keys if value.get(key) in (None, "", [], {})]
    if missing:
        raise ValueError("Missing declared fields: " + ", ".join(missing))


def _refs(workspace: Workspace, ids: list[str]) -> dict:
    return {rid: workspace.validate_current(rid)["revision"] for rid in ids}


def _owned_file(workspace: Workspace, filename: str) -> Path:
    root = workspace.root.resolve()
    path = (root / filename).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("Select an existing file inside the research workspace")
    return path


class Governance:
    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    def panel(self, spec: dict) -> dict:
        """Create a panel contract with declared estimand, limits and cut criteria."""
        _required(spec, ("title", "question", "estimand", "input_ids", "independent_unit",
                         "hierarchy", "analysis_plan", "permitted_claims", "prohibited_claims",
                         "alternatives", "qc", "sensitivity", "cut_criteria"))
        revisions = _refs(self.workspace, spec["input_ids"])
        return self.workspace.create_record("note", spec["title"], json.dumps(spec, indent=2),
            metadata={"host_type": "panel_contract", "state": "mapped", "contract": spec,
                      "input_revisions": revisions}, links=list(revisions))

    def start_review(self, title: str, baseline_ids: list[str], files: list[str],
                     *, round_label: str, submission_status: str = "mock") -> dict:
        """Freeze exact baseline bytes and record snapshots; never submits externally."""
        if submission_status not in {"mock", "owner_reported_submitted"}:
            raise ValueError("submission_status must be mock or owner_reported_submitted")
        if not baseline_ids or not files or not title.strip() or not round_label.strip():
            raise ValueError("Review intake needs a title, round, records and exact files")
        revisions = _refs(self.workspace, baseline_ids)
        snapshots = [self.workspace.get_record(rid) for rid in baseline_ids]
        copied = []
        for filename in files:
            path = _owned_file(self.workspace, filename)
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            target = self.workspace.root / "review_baselines" / digest / path.name
            if not target.resolve().is_relative_to(self.workspace.root.resolve()):
                raise ValueError("Baseline destination escapes the workspace")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != data:
                raise RuntimeError("Frozen baseline was changed")
            if not target.exists():
                with target.open("xb") as stream:
                    stream.write(data)
            copied.append({"original": str(path.relative_to(self.workspace.root.resolve())),
                           "snapshot": str(target.relative_to(self.workspace.root)),
                           "sha256": digest, "bytes": len(data)})
        # Historical snapshots deliberately do not depend on live records: a later
        # revision is expected, and must not rewrite the submitted baseline.
        return self.workspace.create_record("note", title, "Frozen review intake: " + round_label,
            metadata={"host_type": "review_round", "round": round_label,
                      "submission_status": submission_status, "baseline_records": snapshots,
                      "baseline_revisions": revisions, "files": copied, "requests": []})

    def review_request(self, review_id: str, expected_revision: int, request: dict) -> dict:
        """Add or replace an atomic request; keep prior request revisions in history."""
        _required(request, ("request_id", "verbatim", "source_locator", "disposition",
                            "rationale", "inventory_consulted", "needs_experiment"))
        if request["disposition"] not in {"clarify", "rewrite", "reanalyze", "new_experiment",
                                          "decline", "needs_decision"}:
            raise ValueError("Unrecognized response disposition")
        if type(request["needs_experiment"]) is not bool:
            raise ValueError("needs_experiment must be explicit")
        request = deepcopy(request)
        request["evidence_revisions"] = _refs(self.workspace, request.get("evidence_ids", []))
        with self.workspace.transaction():
            record = self.workspace.get_record(review_id)
            if record["metadata"].get("host_type") != "review_round":
                raise ValueError("Select a review round")
            metadata = deepcopy(record["metadata"])
            metadata["requests"] = [r for r in metadata["requests"]
                                    if r["request_id"] != request["request_id"]] + [request]
            return self.workspace.update_record(review_id, expected_revision=expected_revision,
                                                metadata=metadata)

    def check_review(self, review_id: str, package: dict | None = None) -> dict:
        """Check frozen bytes, coverage and clean/marked/response location reports."""
        record = self.workspace.get_record(review_id)
        if record["metadata"].get("host_type") != "review_round":
            raise ValueError("Select a review round")
        findings = []
        for item in record["metadata"]["files"]:
            path = _owned_file(self.workspace, item["snapshot"])
            if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                findings.append({"code": "baseline_changed", "file": item["snapshot"]})
        requests = record["metadata"]["requests"]
        if not requests:
            findings.append({"code": "no_requests"})
        for request in requests:
            rid = request["request_id"]
            if request["disposition"] == "needs_decision":
                findings.append({"code": "unresolved_disposition", "request_id": rid})
            if request["needs_experiment"] and not request.get("scientist_decision"):
                findings.append({"code": "experiment_decision_required", "request_id": rid})
            for field in ("response", "current_locator", "change_summary"):
                if not request.get(field):
                    findings.append({"code": "missing_" + field, "request_id": rid})
            for eid in request.get("evidence_ids", []):
                try:
                    current = self.workspace.validate_current(eid)
                    if current["revision"] != request.get("evidence_revisions", {}).get(eid):
                        findings.append({"code": "stale_request_evidence", "request_id": rid})
                except RuntimeError:
                    findings.append({"code": "stale_request_evidence", "request_id": rid})
        if package is not None:
            for field in ("clean", "marked", "response"):
                if not package.get(field):
                    findings.append({"code": "missing_package_" + field})
                else:
                    _owned_file(self.workspace, package[field])
            ids = {request["request_id"] for request in requests}
            if set(package.get("covered_request_ids", [])) != ids:
                findings.append({"code": "request_coverage_mismatch"})
            if not package.get("consistency_review"):
                findings.append({"code": "human_consistency_review_required"})
        return {"review_id": review_id, "findings": findings,
                "mechanically_complete": not findings,
                "scientific_approval": False,
                "limitation": "Semantic adequacy and exact visual consistency require review."}

    def capture_problem(self, spec: dict) -> dict:
        _required(spec, ("title", "observed", "expected", "reproduction", "classification",
                         "owner", "next_check"))
        if spec["classification"] not in {"minor_safe", "material_scientific", "accepted_limit"}:
            raise ValueError("Declare minor_safe, material_scientific or accepted_limit")
        return self.workspace.create_record("note", spec["title"], json.dumps(spec, indent=2),
            metadata={"host_type": "workflow_problem", "state": "open", "problem": spec})

    def resolve_problem(self, problem_id: str, expected_revision: int, resolution: dict) -> dict:
        _required(resolution, ("cause", "fix", "representative_verification", "procedure",
                              "version", "applicability_limits", "attributed_to"))
        with self.workspace.transaction():
            record = self.workspace.get_record(problem_id)
            if record["metadata"].get("host_type") != "workflow_problem":
                raise ValueError("Select a workflow problem")
            metadata = deepcopy(record["metadata"])
            if (metadata["problem"]["classification"] == "material_scientific"
                    and not resolution.get("scientist_decision")):
                raise ValueError("A material scientific policy change needs a scientist decision")
            metadata.update(state="monitoring", resolution=resolution)
            return self.workspace.update_record(problem_id, expected_revision=expected_revision,
                                                metadata=metadata)
