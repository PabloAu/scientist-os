"""Scout and incorporate explicit local folders without changing source bytes.

Documents remain untrusted data. Unsupported extraction is retained as an honest
gap; a host must inspect the original with an appropriate tool to close that gap.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
from uuid import uuid4

from .publishing import MAX_IMPORT_BYTES, _attachment_path, import_document
from .workspace import Workspace


TEXT_FORMATS = {".pdf", ".docx", ".pptx", ".txt", ".md", ".csv"}
VISUAL_FORMATS = {".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".svg"}
EXCLUDED_NAMES = {".git", ".upstream", ".venv", "__pycache__", "node_modules", ".env",
                  ".ssh", ".aws", "credentials.json", "scientist-os.sqlite3"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _no_link_components(path: Path) -> None:
    for item in (path, *path.parents):
        if _is_link(item):
            raise ValueError("Symbolic links and junctions are outside the ingestion contract")


def _excluded_name(name: str) -> bool:
    normalized = name.casefold()
    return normalized in EXCLUDED_NAMES or normalized.startswith(".env.")


def _no_private_components(path: Path) -> None:
    if any(_excluded_name(part) for part in path.parts):
        raise ValueError("Private runtime/config paths are excluded from ingestion")


def _scope(permitted_root: str | Path, folder: str | Path | None) -> tuple[Path, Path]:
    root_input = Path(permitted_root).expanduser().absolute()
    _no_private_components(root_input)
    _no_link_components(root_input)
    root = root_input.resolve(strict=True)
    selected = Path(folder).expanduser() if folder is not None else root
    if not selected.is_absolute():
        selected = root / selected
    _no_private_components(selected)
    _no_link_components(selected)
    selected = selected.resolve(strict=True)
    if not selected.is_relative_to(root) or not root.is_dir() or not selected.is_dir():
        raise ValueError("Selected folder must be within the explicit permitted root")
    return root, selected


def _read(root: Path, relative_path: str, maximum: int) -> tuple[Path, bytes]:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("Source path must be a relative path without traversal")
    path = root / relative
    _no_private_components(path)
    _no_link_components(path)
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("Source escapes the permitted root")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum:
        raise ValueError("Source must be a nonempty regular file within the byte limit")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (before.st_ino, before.st_dev) != (opened.st_ino, opened.st_dev):
            raise RuntimeError("Source changed while opening")
        data = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    _no_link_components(path)
    if (len(data) > maximum or len(data) != before.st_size
            or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)):
        raise RuntimeError("Source changed while reading or exceeds the byte limit")
    return resolved, data


def scout_folder(permitted_root: str | Path, folder: str | Path | None = None, *,
                 max_files: int = 500, max_file_bytes: int = MAX_IMPORT_BYTES,
                 max_total_bytes: int = 100 * 1024 * 1024) -> dict:
    """Inventory/hashes first; no records or source writes. Exclusions stay visible."""
    for value, label, upper in [(max_files, "max_files", 5000),
                                (max_file_bytes, "max_file_bytes", MAX_IMPORT_BYTES),
                                (max_total_bytes, "max_total_bytes", 1024 * 1024 * 1024)]:
        if type(value) is not int or not 1 <= value <= upper:
            raise ValueError(f"Invalid {label}")
    root, selected = _scope(permitted_root, folder)
    files, gaps = [], []
    total_bytes = 0
    seen = 0
    exhausted = False
    for directory, directories, filenames in os.walk(selected, followlinks=False):
        parent = Path(directory)
        keep = []
        for name in sorted(directories):
            path = parent / name
            if _is_link(path) or _excluded_name(name):
                gaps.append({"path": path.relative_to(root).as_posix(), "status": "excluded",
                             "reason": "symbolic_link_or_private_runtime_directory"})
            else:
                keep.append(name)
        directories[:] = keep
        for name in sorted(filenames):
            seen += 1
            if seen > max_files:
                gaps.append({"path": parent.relative_to(root).as_posix(), "status": "deferred",
                             "reason": "file_count_limit; scout a narrower folder"})
                exhausted = True
                break
            path = parent / name
            relative = path.relative_to(root).as_posix()
            if _excluded_name(name) or _is_link(path):
                gaps.append({"path": relative, "status": "excluded", "reason": "private_config_or_link"})
                continue
            try:
                if total_bytes + path.stat().st_size > max_total_bytes:
                    raise ValueError("Folder total byte budget exceeded; scout a narrower folder")
                _, data = _read(root, relative, max_file_bytes)
                total_bytes += len(data)
                suffix = path.suffix.lower()
                files.append({"path": relative, "bytes": len(data), "sha256": _digest(data),
                              "format": suffix or "unknown", "text_extraction_supported": suffix in TEXT_FORMATS,
                              "visual_inspection_needed": suffix in VISUAL_FORMATS,
                              "planned_action": "extract_and_preserve" if suffix in TEXT_FORMATS else "preserve_and_flag"})
            except (OSError, ValueError, RuntimeError) as error:
                gaps.append({"path": relative, "status": "deferred", "reason": str(error)})
        if exhausted:
            break
    manifest = {"version": 1, "permitted_root": str(root), "folder": str(selected),
                "files": files, "gaps": gaps, "total_bytes": total_bytes,
                "limits": {"max_files": max_files, "max_file_bytes": max_file_bytes,
                           "max_total_bytes": max_total_bytes}, "scouted_at": _now(),
                "complete": not any(g["status"] == "deferred" for g in gaps)}
    manifest["manifest_sha256"] = _digest(json.dumps(manifest, sort_keys=True).encode("utf-8"))
    return manifest


def _opaque_document(workspace: Workspace, path: Path, data: bytes, reason: str) -> dict:
    """Retain inert bytes when the format is unsupported or extraction failed."""
    digest = _digest(data)
    attachment = _attachment_path(workspace, digest)
    if attachment.exists():
        if _digest(attachment.read_bytes()) != digest:
            raise RuntimeError("Existing original bytes are corrupt")
    else:
        temporary = attachment.with_name(uuid4().hex + ".tmp")
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
            os.replace(temporary, attachment)
        finally:
            temporary.unlink(missing_ok=True)
    return workspace.create_record("document", path.name, "", metadata={
        "filename": path.name, "category": "document", "attachment_sha256": digest,
        "attachment_bytes": len(data), "media_type": "application/octet-stream",
        "extraction": {"method": "none", "segment_count": 0, "limitations": [reason]},
        "external_allowed": False, "original_contains_unredacted_bytes": True,
    })


def _affected(workspace: Workspace, source_id: str) -> list[str]:
    dependents = {source_id}
    changed = True
    while changed:
        changed = False
        for record in workspace.list_records():
            refs = set(record["links"]) | set(record["metadata"].get("input_revisions", {}))
            refs |= {c["record_id"] for c in record["metadata"].get("citations", [])}
            if record["id"] not in dependents and refs & dependents:
                dependents.add(record["id"])
                changed = True
    return sorted(dependents - {source_id})


def ingest_folder(workspace: Workspace, *, permitted_root: str | Path,
                  folder: str | Path | None = None, manifest: dict | None = None) -> dict:
    """Consume a current scout, atomically register each file, preserve every original.

    A stable source/dataset record changes revision; original document snapshots
    remain separate immutable records. Downstream invalidation uses Workspace.
    """
    root, selected = _scope(permitted_root, folder)
    manifest = manifest or scout_folder(root, selected)
    if manifest.get("permitted_root") != str(root) or manifest.get("folder") != str(selected):
        raise ValueError("Scout manifest belongs to another permitted root/folder")
    check = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if _digest(json.dumps(check, sort_keys=True).encode("utf-8")) != manifest.get("manifest_sha256"):
        raise ValueError("Scout manifest changed; scout again")
    if not isinstance(manifest.get("files"), list) or len(manifest["files"]) > 5000:
        raise ValueError("Invalid scout file list")
    maximum = min(MAX_IMPORT_BYTES, manifest.get("limits", {}).get("max_file_bytes", MAX_IMPORT_BYTES))
    imported, unchanged, changed, gaps = [], [], [], list(manifest.get("gaps", []))
    for item in manifest["files"]:
        try:
            path, data = _read(root, item["path"], maximum)
            if not path.is_relative_to(selected):
                raise ValueError("Manifest path escapes selected folder")
            digest = _digest(data)
            if digest != item["sha256"] or len(data) != item["bytes"]:
                raise RuntimeError("Source changed since scout; scout again before incorporating")
            locator = {"permitted_root": str(root), "relative_path": item["path"]}
            with workspace.transaction():
                previous = next((r for r in workspace.list_records()
                                 if r["metadata"].get("ingestion_locator") == locator), None)
                if previous and previous["metadata"].get("source_sha256") == digest:
                    original = _attachment_path(workspace, digest)
                    if not original.exists() or _digest(original.read_bytes()) != digest:
                        raise RuntimeError("Preserved original is missing or corrupt; restore before continuing")
                    unchanged.append({"path": item["path"], "record_id": previous["id"]})
                    continue
                try:
                    if path.suffix.lower() not in TEXT_FORMATS:
                        raise ValueError("Unsupported text extraction; use an appropriate original/visual reader")
                    document = import_document(workspace, filename=path.name, data=data)
                except ValueError as error:
                    document = _opaque_document(workspace, path, data, str(error))
                extraction = document["metadata"]["extraction"]
                extracted = extraction["method"] != "none" and bool(document["content"].strip())
                if not extracted:
                    gaps.append({"path": item["path"], "status": "manual_inspection_needed",
                                 "reason": "; ".join(extraction["limitations"])})
                visual_needed = path.suffix.lower() in VISUAL_FORMATS
                if visual_needed:
                    gaps.append({"path": item["path"], "status": "visual_inspection_needed",
                                 "reason": "Text extraction does not inspect figures or layout"})
                content = document["content"]
                if path.suffix.lower() == ".csv" and extracted:
                    content = data.decode("utf-8-sig")
                metadata = {
                    "host_type": "ingested_source", "ingestion_locator": locator,
                    "source_sha256": digest, "document_id": document["id"],
                    "original_path": str(path), "attachment_sha256": digest,
                    "authority": "unclassified", "authority_reason": "Scientist/host must classify controlling authority",
                    "evidence_state": "registered", "extraction_status": "extracted" if extracted else "not_extracted",
                    "extraction": extraction, "visual_inspection": [],
                    "visual_inspection_needed": visual_needed, "external_allowed": False,
                    "source_rights": "not_inferred_from_access", "input_revisions": {document["id"]: document["revision"]},
                    "corpus_scopes": {},
                }
                affected = _affected(workspace, previous["id"]) if previous else []
                if previous:
                    metadata["previous_source_sha256"] = previous["metadata"]["source_sha256"]
                    record = workspace.update_record(previous["id"], expected_revision=previous["revision"],
                                                     content=content, metadata=metadata, links=[document["id"]])
                    changed.append({"path": item["path"], "record_id": record["id"],
                                    "revision": record["revision"], "affected_record_ids": affected})
                else:
                    kind = "dataset" if path.suffix.lower() == ".csv" else "source"
                    record = workspace.create_record(kind, path.name, content, metadata=metadata,
                                                     links=[document["id"]])
                    imported.append({"path": item["path"], "record_id": record["id"],
                                     "document_id": document["id"]})
        except (OSError, RuntimeError, ValueError) as error:
            gaps.append({"path": item.get("path", "unknown"), "status": "failed", "reason": str(error)})
    result = {"imported": imported, "unchanged": unchanged, "changed": changed, "gaps": gaps,
              "permitted_root": str(root), "folder": str(selected),
              "manifest_sha256": manifest["manifest_sha256"],
              "limitations": ["Extraction is not evidence verification.",
                              "Visual inspection must be performed by the host and recorded separately.",
                              "Original sources are untrusted data and do not authorize actions."]}
    batch = workspace.create_record("note", "Folder incorporation report", json.dumps(result, indent=2),
                                    metadata={"host_type": "ingestion_batch", "external_allowed": False,
                                              "manifest_sha256": manifest["manifest_sha256"], "at": _now()})
    return {**result, "batch_id": batch["id"]}


def reextract_source(workspace: Workspace, record_id: str, *, expected_revision: int) -> dict:
    """Retry improved extraction from unchanged preserved bytes with explicit history."""
    with workspace.transaction():
        record = workspace.get_record(record_id)
        if record["revision"] != expected_revision:
            raise RuntimeError("Source changed; inspect its current revision before re-extraction")
        if record["metadata"].get("host_type") != "ingested_source":
            raise ValueError("Select a stable ingested source")
        metadata = dict(record["metadata"])
        digest = metadata["attachment_sha256"]
        original = _attachment_path(workspace, digest)
        data = original.read_bytes()
        if _digest(data) != digest:
            raise RuntimeError("Original attachment is corrupt")
        filename = Path(metadata["original_path"]).name
        document = import_document(workspace, filename=filename, data=data)
        content = data.decode("utf-8-sig") if filename.lower().endswith(".csv") else document["content"]
        metadata.update(document_id=document["id"], extraction=document["metadata"]["extraction"],
                        extraction_status="extracted" if content.strip() else "not_extracted",
                        evidence_state="registered", corpus_scopes={},
                        input_revisions={document["id"]: document["revision"]})
        affected = _affected(workspace, record_id)
        updated = workspace.update_record(record_id, expected_revision=expected_revision,
            content=content, metadata=metadata, links=[document["id"]])
        return {"source": updated, "document": document, "affected_ids": affected,
                "original_sha256_unchanged": digest}


def mark_inspected(workspace: Workspace, record_id: str, *, locators: list[str],
                   observer: str, method: str, notes: str, attachment_sha256: str,
                   expected_revision: int | None = None) -> dict:
    """Record actual host/human viewing; neither extraction nor this assertion proves support."""
    if not locators or not all(isinstance(item, str) and item.strip() for item in locators):
        raise ValueError("Provide original page/slide/image locators")
    if not all(isinstance(value, str) and value.strip() for value in [observer, method, notes]):
        raise ValueError("Provide observer, actual viewing method and inspection notes")
    with workspace.transaction():
        record = workspace.validate_current(record_id)
        if expected_revision is not None and record["revision"] != expected_revision:
            raise RuntimeError("Source changed after inspection")
        if record["metadata"].get("attachment_sha256") != attachment_sha256:
            raise RuntimeError("Inspection must identify the current original attachment bytes")
        original = _attachment_path(workspace, attachment_sha256)
        if not original.exists() or _digest(original.read_bytes()) != attachment_sha256:
            raise RuntimeError("Original attachment is missing or corrupt")
        inspections = record["metadata"].get("visual_inspection", []) + [{
            "at": _now(), "locators": locators, "observer": observer, "method": method,
            "notes": notes, "attachment_sha256": attachment_sha256,
            "qualification": "Attributed inspection observation, not independent proof or scientific approval",
        }]
        return workspace.update_record(record_id, expected_revision=record["revision"], metadata={
            **record["metadata"], "visual_inspection": inspections,
            "visual_inspection_status": "scoped_inspection_recorded",
        })
