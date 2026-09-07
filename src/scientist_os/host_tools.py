"""Scientific operations for a tool-capable host; no hidden model/API client."""
from __future__ import annotations

from copy import deepcopy
from functools import partial
import hashlib
import inspect
import json
from pathlib import Path

from . import __version__
from .workspace import Workspace


class HostTools:
    """Bindings fix filesystem scope outside model-provided operation arguments.

    This is a single-user tool interface, not a Python execution sandbox. Host
    permissions govern general tools. Explicitly selected roots may be disclosed
    to the configured host/model; local storage does not imply local inference.
    """

    def __init__(self, workspace: Workspace, permitted_roots: list[str] | None = None):
        self.workspace = workspace
        self.roots = [workspace.root.resolve(), *[Path(p).resolve() for p in permitted_roots or []]]

    def _path(self, value: str, *, exists: bool = True) -> Path:
        path = Path(value).resolve()
        if not any(path.is_relative_to(root) for root in self.roots):
            raise ValueError("Path is outside the host connection's permitted roots")
        if exists and not path.exists():
            raise ValueError("Selected path does not exist")
        return path

    def _ingest(self, permitted_root: str, folder: str | None = None,
                manifest: dict | None = None):
        from .ingestion import ingest_folder
        self._path(permitted_root)
        return ingest_folder(self.workspace, permitted_root=permitted_root,
                             folder=folder, manifest=manifest)

    def _scout(self, permitted_root: str, folder: str | None = None,
               max_files: int = 500, max_file_bytes: int = 20 * 1024 * 1024,
               max_total_bytes: int = 100 * 1024 * 1024):
        from .ingestion import scout_folder
        self._path(permitted_root)
        return scout_folder(permitted_root, folder, max_files=max_files,
                            max_file_bytes=max_file_bytes, max_total_bytes=max_total_bytes)

    def _run(self, spec: dict) -> dict:
        from .execution import run_python
        spec = deepcopy(spec)
        self._path(spec["repo_path"])
        for entry in spec.get("inputs", []):
            self._path(entry["path"])
        spec["permitted_roots"] = [str(root) for root in self.roots]
        return run_python(self.workspace, spec)

    def _register_result(self, run_id: str, result_file: str, figure_title: str) -> dict:
        """Link an explicitly selected supported result JSON to its verified execution."""
        from .execution import verify_run
        from .science import render_figure
        from .service import create_figure
        verification = verify_run(self.workspace, run_id)
        if not verification["intact"] or verification["current_source_changes"]:
            raise RuntimeError("Run or current evidence changed; inspect before registering outputs")
        run = self.workspace.get_run(run_id)
        if run.get("status") != "completed" or run.get("type") != "python_execution":
            raise ValueError("Select a successfully completed Python execution")
        root = Path(run["manifest_path"]).parent.resolve()
        path = (root / "outputs" / result_file).resolve()
        if (not root.is_relative_to(self.workspace.root.resolve())
                or not path.is_relative_to(root / "outputs") or result_file not in run["outputs"]):
            raise ValueError("Select an exact output file from this run")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != run["outputs"][result_file]["sha256"]:
            raise RuntimeError("Selected result file was modified")
        result = json.loads(data)
        render_figure(result, title=figure_title)  # validate supported result semantics/geometry
        source = next((r for r in self.workspace.list_records("analysis")
                       if r["metadata"].get("execution_run_id") == run_id), None)
        if source is None:
            raise ValueError("Execution has no current linked analysis record")
        self.workspace.validate_current(source["id"])
        with self.workspace.transaction():
            metadata = deepcopy(source["metadata"])
            metadata.update(result=result, figure_title=figure_title,
                            selected_result_file=result_file,
                            selected_result_sha256=run["outputs"][result_file]["sha256"],
                            input_revisions={source["id"]: source["revision"]})
            analysis = self.workspace.create_record("analysis", figure_title,
                json.dumps(result, indent=2), metadata=metadata, links=[source["id"]])
            output = create_figure(self.workspace, analysis)
        return {"analysis": analysis, "output": output, "result": result,
                "execution_run_id": run_id, "selected_result_sha256": metadata["selected_result_sha256"]}

    def _read(self, record_id: str, offset: int = 0, limit: int = 24000) -> dict:
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100000:
            raise ValueError("Use nonnegative offset and a limit between 1 and 100000")
        record = self.workspace.get_record(record_id)
        length = len(record["content"])
        record["content"] = record["content"][offset:offset + limit]
        record.update(untrusted_source_content=True, offset=offset, total_characters=length,
                      next_offset=offset + limit if offset + limit < length else None)
        return record

    def _list(self, kind: str | None = None, limit: int = 100, offset: int = 0) -> dict:
        if not 1 <= limit <= 500 or offset < 0:
            raise ValueError("Invalid pagination")
        rows = self.workspace.list_records(kind)
        return {"total": len(rows), "records": [{k: r[k] for k in
            ("id", "kind", "title", "revision", "sha256", "review_status", "metadata", "links")}
            for r in rows[offset:offset + limit]],
            "next_offset": offset + limit if offset + limit < len(rows) else None}

    def _manuscript(self, *, title: str, sections: list[dict], source_ids: list[str],
                    reports: dict) -> dict:
        from .studio import create_manuscript
        if not reports or not source_ids:
            raise ValueError("Declare source_ids and claim/citation/terminology/change reports")
        with self.workspace.transaction():
            revisions = {rid: self.workspace.validate_current(rid)["revision"] for rid in source_ids}
            record = create_manuscript(self.workspace, title=title, sections=sections)
            metadata = deepcopy(record["metadata"])
            metadata["accepted_evidence_revisions"] = revisions
            metadata["input_revisions"].update(revisions)
            metadata["writing_reports"] = reports
            return self.workspace.update_record(record["id"], expected_revision=record["revision"],
                metadata=metadata, links=list(metadata["input_revisions"]))

    def _revise(self, record_id: str, expected_revision: int, section_id: str,
                selected_text: str, replacement: str, reason: str, attributed_to: str) -> dict:
        """Apply a conversationally requested unique exact passage edit as a draft."""
        from .studio import update_manuscript
        if not selected_text or not reason.strip() or not attributed_to.strip():
            raise ValueError("Provide exact selected text, reason and actual actor")
        with self.workspace.transaction():
            record = self.workspace.validate_current(record_id)
            if record["revision"] != expected_revision:
                raise RuntimeError("Manuscript changed since selection")
            sections = deepcopy(record["metadata"].get("sections", []))
            section = next((s for s in sections if s["id"] == section_id), None)
            if section is None or section["text"].count(selected_text) != 1:
                raise ValueError("Select one unique exact passage in the requested section")
            section["text"] = section["text"].replace(selected_text, replacement, 1)
            updated = update_manuscript(self.workspace, record_id,
                                       expected_revision=expected_revision, sections=sections)
            metadata = deepcopy(updated["metadata"])
            metadata["last_conversational_edit"] = {"section_id": section_id,
                "selected_text": selected_text, "replacement": replacement, "reason": reason,
                "attributed_to": attributed_to, "scientific_approval": False}
            return self.workspace.update_record(record_id, expected_revision=updated["revision"],
                                                metadata=metadata)

    def _export(self, record_id: str, format: str) -> dict:
        from .publishing import export_manuscript, export_presentation, publication_figure
        record = self.workspace.validate_current(record_id)
        if record["kind"] == "manuscript" and format in {"docx", "html"}:
            data = export_manuscript(self.workspace, record_id, format=format)
        elif record["kind"] == "presentation" and format == "pptx":
            data = export_presentation(self.workspace, record_id)
        elif record["kind"] == "output" and format == "png":
            data = publication_figure(self.workspace, record_id)
        elif format in {"md", "svg", "json", "txt"}:
            if format == "svg" and record["metadata"].get("format") != "svg":
                raise ValueError("Record is not an SVG figure")
            data = (json.dumps(record, indent=2, ensure_ascii=False) if format == "json"
                    else record["content"]).encode("utf-8")
        else:
            raise ValueError("Unsupported record/format pair")
        digest = hashlib.sha256(data).hexdigest()
        target = self.workspace.root / "exports" / record_id / f"r{record['revision']}" / f"{digest[:16]}.{format}"
        if not target.resolve().is_relative_to(self.workspace.root.resolve()):
            raise ValueError("Export destination escapes the workspace")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != data:
                raise RuntimeError("Previously exported bytes were modified")
        else:
            with target.open("xb") as stream:
                stream.write(data)
        return {"path": str(target.resolve()), "sha256": digest, "bytes": len(data),
                "record_id": record_id, "revision": record["revision"],
                "scientific_approval": record["review_status"], "visual_inspection": "pending"}

    def _inspect_artifact(self, path: str, sha256: str, record_id: str,
                          locators: list[str], observer: str, findings: str,
                          method: str) -> dict:
        file = self._path(path)
        if hashlib.sha256(file.read_bytes()).hexdigest() != sha256:
            raise RuntimeError("Inspect the exact exported bytes before registering review")
        if not locators or not observer.strip() or not method.strip():
            raise ValueError("Specify inspected pages/slides/panels, observer and actual method")
        record = self.workspace.validate_current(record_id)
        return self.workspace.create_record("note", "Artifact inspection: " + file.name, findings,
            metadata={"host_type": "artifact_inspection", "path": str(file), "sha256": sha256,
                      "locators": locators, "observer": observer, "method": method,
                      "inspection_is_attributed": True,
                      "input_revisions": {record_id: record["revision"]}}, links=[record_id])

    def operations(self) -> dict:
        from .host_state import HostState
        from .ingestion import mark_inspected, reextract_source
        from .execution import verify_run, replay_run, recover_run
        from .meta_review import MetaReview
        from .governance import Governance
        from . import publishing, studio, service
        state, meta, governance = HostState(self.workspace), MetaReview(self.workspace), Governance(self.workspace)
        return {
            "project.start": state.start_project, "project.context": state.context,
            "project.remember": state.remember, "project.export": state.export_context,
            "task.create": state.task, "task.checkpoint": state.checkpoint,
            "task.begin_action": state.begin_action, "task.finish_action": state.finish_action,
            "task.recover": state.recover, "science.record": state.record_science,
            "task.reconcile_action": state.reconcile_action,
            "science.reconcile": state.reconcile_experiment, "science.advance": state.advance_evidence,
            "ingest.scout": self._scout, "ingest.folder": self._ingest,
            "ingest.inspect": partial(mark_inspected, self.workspace),
            "ingest.reextract": partial(reextract_source, self.workspace),
            "record.list": self._list, "record.read": self._read,
            "record.search": self.workspace.search, "record.create": self.workspace.create_record,
            "record.update": self.workspace.update_record, "record.validate": self.workspace.validate_current,
            "analysis.summary": partial(service.analyze, self.workspace), "analysis.run": self._run,
            "analysis.register_result": self._register_result,
            "analysis.verify": partial(verify_run, self.workspace),
            "analysis.replay": partial(replay_run, self.workspace),
            "analysis.recover": partial(recover_run, self.workspace),
            "meta.create": meta.create, "meta.update": meta.update, "meta.check": meta.check,
            "meta.freeze": meta.freeze, "meta.synthesize": meta.synthesize,
            "manuscript.create": self._manuscript, "manuscript.revise": self._revise,
            "manuscript.update": partial(studio.update_manuscript, self.workspace),
            "reference.create": partial(studio.create_reference, self.workspace),
            "presentation.create": partial(publishing.create_presentation, self.workspace),
            "presentation.update": partial(publishing.update_presentation, self.workspace),
            "artifact.export": self._export, "artifact.inspect": self._inspect_artifact,
            "panel.create": governance.panel, "review.start": governance.start_review,
            "review.request": governance.review_request, "review.check": governance.check_review,
            "problem.capture": governance.capture_problem, "problem.resolve": governance.resolve_problem,
        }

    def catalog(self) -> dict:
        return {"version": __version__, "runtime": "host_supplied_inference_and_general_tools",
                "permitted_roots": [str(p) for p in self.roots],
                "operations": {name: {"signature": str(inspect.signature(fn)),
                    "description": inspect.getdoc(fn.func if isinstance(fn, partial) else fn)
                        or "See the Scientist OS procedure and API guide."}
                    for name, fn in self.operations().items()}}

    def call(self, operation: str, arguments: dict) -> dict:
        if not isinstance(arguments, dict):
            raise ValueError("Operation arguments must be a JSON object")
        operations = self.operations()
        if operation not in operations:
            raise ValueError("Unknown scientific operation; inspect catalog")
        preflight = self.workspace.save_run({"type": "host_operation", "status": "started",
            "operation": operation, "arguments": arguments, "software_version": __version__,
            "inference": "provided_by_calling_host; hidden context and usage not observable"})
        try:
            result = operations[operation](**arguments)
        except Exception as error:
            self.workspace.save_run({"type": "host_operation", "status": "failed",
                "preflight_id": preflight["id"], "operation": operation, "error": str(error)})
            raise
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False)
        retained = result if len(encoded.encode("utf-8")) < 2_000_000 else {
            "result_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
            "result_bytes": len(encoded.encode("utf-8")),
            "note": "Large result returned to host; retrieve canonical records for full content."}
        self.workspace.save_run({"type": "host_operation", "status": "completed",
            "preflight_id": preflight["id"], "operation": operation,
            "result": retained, "scientific_approval": False})
        return result
