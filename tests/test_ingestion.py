import hashlib
import json

import pytest

from scientist_os.ingestion import ingest_folder, mark_inspected, scout_folder
from scientist_os.publishing import attachment_bytes
from scientist_os.workspace import Workspace


def test_mixed_scout_idempotence_original_bytes_and_gaps(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "notes.md").write_text("# Experiment\nFictional note", encoding="utf-8")
    (sources / "data.csv").write_text("day,value\na,1\nb,3\n", encoding="utf-8")
    (sources / "image.tiff").write_bytes(b"fictional opaque bytes")
    (sources / ".env").write_text("TOKEN=not-for-ingestion")
    workspace = Workspace(tmp_path / "workspace")
    before = {p.name: p.read_bytes() for p in sources.iterdir()}
    manifest = scout_folder(sources)
    assert len(manifest["files"]) == 3
    assert any(gap["status"] == "excluded" for gap in manifest["gaps"])
    result = ingest_folder(workspace, permitted_root=sources, manifest=manifest)
    assert len(result["imported"]) == 3
    assert any(gap["status"] == "manual_inspection_needed" for gap in result["gaps"])
    second = ingest_folder(workspace, permitted_root=sources)
    assert len(second["unchanged"]) == 3
    assert not second["imported"]
    assert len(workspace.list_records("document")) == 3
    assert workspace.list_records("dataset")[0]["content"] == before["data.csv"].decode("utf-8")
    for record in workspace.list_records("document"):
        original, filename, _ = attachment_bytes(workspace, record["id"])
        assert original == before[filename]
    assert {p.name: p.read_bytes() for p in sources.iterdir()} == before


def test_changed_source_invalidates_transitive_results_and_retains_history(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    file = sources / "data.csv"
    file.write_text("unit,value\na,1\nb,3", encoding="utf-8")
    original_bytes = file.read_bytes()
    workspace = Workspace(tmp_path / "workspace")
    first = ingest_folder(workspace, permitted_root=sources)
    dataset = workspace.get_record(first["imported"][0]["record_id"])
    original_document = dataset["metadata"]["document_id"]
    analysis = workspace.create_record("analysis", "Mean", "2", links=[dataset["id"]],
                                       metadata={"input_revisions": {dataset["id"]: dataset["revision"]}})
    claim = workspace.create_record("claim", "Result", "Fictional mean 2", links=[analysis["id"]],
                                    metadata={"input_revisions": {analysis["id"]: analysis["revision"]}})
    file.write_text("unit,value\na,1\nb,5", encoding="utf-8")
    update = ingest_folder(workspace, permitted_root=sources)
    assert len(update["changed"]) == 1
    assert set(update["changed"][0]["affected_record_ids"]) == {analysis["id"], claim["id"]}
    assert update["changed"][0]["record_id"] == dataset["id"]
    with pytest.raises(RuntimeError, match="stale"):
        workspace.validate_current(claim["id"])
    assert attachment_bytes(workspace, original_document)[0] == original_bytes
    assert len(workspace.list_records("document")) == 2
    assert any(event["action"] == "dependency_invalidated" for event in workspace.events())


def test_source_changed_after_scout_is_gap_not_silent_update(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    file = sources / "note.txt"
    file.write_text("before")
    manifest = scout_folder(sources)
    file.write_text("after")
    workspace = Workspace(tmp_path / "workspace")
    result = ingest_folder(workspace, permitted_root=sources, manifest=manifest)
    assert not result["imported"]
    assert result["gaps"][0]["status"] == "failed"
    assert "changed since scout" in result["gaps"][0]["reason"]


def test_scope_manifest_and_size_boundaries(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (sources / "large.txt").write_text("too large")
    with pytest.raises(ValueError, match="permitted root"):
        scout_folder(sources, outside)
    with pytest.raises(ValueError, match="Invalid max"):
        scout_folder(sources, max_file_bytes=30 * 1024 * 1024)
    manifest = scout_folder(sources, max_file_bytes=3)
    assert not manifest["files"] and not manifest["complete"]
    original = scout_folder(sources)
    original["files"][0]["path"] = "../outside/secret.txt"
    with pytest.raises(ValueError, match="manifest changed"):
        ingest_folder(Workspace(tmp_path / "workspace"), permitted_root=sources, manifest=original)


def test_rehashed_manifest_cannot_escape_root(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "note.txt").write_text("x")
    (tmp_path / "outside.txt").write_text("private")
    manifest = scout_folder(sources)
    manifest["files"][0]["path"] = "../outside.txt"
    del manifest["manifest_sha256"]
    manifest["manifest_sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    result = ingest_folder(Workspace(tmp_path / "workspace"), permitted_root=sources, manifest=manifest)
    assert not result["imported"]
    assert "traversal" in result["gaps"][0]["reason"]


def test_symlinks_not_followed(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    outside = tmp_path / "private.txt"
    outside.write_text("must not import")
    try:
        (sources / "linked.txt").symlink_to(outside)
    except OSError:
        pytest.skip("Host does not grant symlink creation")
    manifest = scout_folder(sources)
    assert not manifest["files"]
    assert manifest["gaps"][0]["status"] == "excluded"


def test_scoped_inspection_bound_to_original_hash_and_reset_on_change(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "figure.png").write_bytes(b"fictional fixture bytes")
    workspace = Workspace(tmp_path / "workspace")
    imported = ingest_folder(workspace, permitted_root=sources)
    record = workspace.get_record(imported["imported"][0]["record_id"])
    with pytest.raises(RuntimeError, match="current original"):
        mark_inspected(workspace, record["id"], locators=["image"], observer="host", method="vision",
                        notes="fictional test assertion", attachment_sha256="0" * 64)
    marked = mark_inspected(workspace, record["id"], locators=["image"], observer="fixture operator",
                            method="fixture assertion only", notes="This test does not perform visual inference",
                            attachment_sha256=record["metadata"]["attachment_sha256"])
    assert marked["metadata"]["visual_inspection_status"] == "scoped_inspection_recorded"
    assert marked["metadata"]["evidence_state"] == "registered"
    (sources / "figure.png").write_bytes(b"changed fixture bytes")
    updated = ingest_folder(workspace, permitted_root=sources)
    current = workspace.get_record(updated["changed"][0]["record_id"])
    assert not current["metadata"]["visual_inspection"]


def test_bad_pdf_retained_with_extraction_gap(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "scanned.pdf").write_bytes(b"not a readable PDF")
    workspace = Workspace(tmp_path / "workspace")
    result = ingest_folder(workspace, permitted_root=sources)
    assert len(result["imported"]) == 1
    assert workspace.get_record(result["imported"][0]["record_id"])["metadata"]["extraction_status"] == "not_extracted"
    assert any("PDF header" in gap["reason"] for gap in result["gaps"])


def test_repeat_import_detects_corrupt_preserved_original(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "note.txt").write_bytes(b"original")
    workspace = Workspace(tmp_path / "workspace")
    first = ingest_folder(workspace, permitted_root=sources)
    record = workspace.get_record(first["imported"][0]["record_id"])
    attachment = workspace.root / "attachments" / record["metadata"]["attachment_sha256"]
    attachment.write_bytes(b"corrupted")
    result = ingest_folder(workspace, permitted_root=sources)
    assert not result["unchanged"]
    assert result["gaps"][0]["status"] == "failed"
    assert "corrupt" in result["gaps"][0]["reason"]


@pytest.mark.parametrize("private_name", [".upstream", ".UPSTREAM", ".ssh", ".git", ".env.private"])
def test_direct_or_nested_private_folder_selection_is_rejected(tmp_path, private_name):
    sources = tmp_path / "sources"
    private = sources / private_name
    nested = private / "nested"
    nested.mkdir(parents=True)
    (nested / "fictional.txt").write_text("Fictional excluded fixture only")
    manifest = scout_folder(sources)
    assert not manifest["files"]
    assert any(gap["path"] == private_name and gap["status"] == "excluded"
               for gap in manifest["gaps"])
    for root, folder in [(sources, private), (sources, nested), (private, None), (nested, None)]:
        with pytest.raises(ValueError, match="Private runtime/config"):
            scout_folder(root, folder)
    workspace = Workspace(tmp_path / "workspace")
    with pytest.raises(ValueError, match="Private runtime/config"):
        ingest_folder(workspace, permitted_root=sources, folder=private)
    assert not workspace.list_records()


def test_rehashed_manifest_cannot_admit_private_path(tmp_path):
    sources = tmp_path / "sources"
    private = sources / ".upstream"
    private.mkdir(parents=True)
    data = b"Fictional excluded fixture only"
    (sources / "public.txt").write_bytes(data)
    (private / "private.txt").write_bytes(data)
    manifest = scout_folder(sources)
    manifest["files"][0]["path"] = ".upstream/private.txt"
    del manifest["manifest_sha256"]
    manifest["manifest_sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    workspace = Workspace(tmp_path / "workspace")
    result = ingest_folder(workspace, permitted_root=sources, manifest=manifest)
    assert not result["imported"]
    assert any(gap["status"] == "failed" and "Private runtime/config" in gap["reason"]
               for gap in result["gaps"])
    assert not workspace.list_records("source")
