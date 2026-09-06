"""Run the installed command-line entry points against real temporary stores."""

import json
import os
import sqlite3
import subprocess
import sys

import pytest

from scientist_os import __version__
from scientist_os.cli import main
from scientist_os.workspace import Workspace


def invoke(*arguments):
    environment = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, "-m", "scientist_os.cli", *map(str, arguments)],
                          capture_output=True, text=True, encoding="utf-8", env=environment, timeout=30)


def test_cli_version_and_help_are_available():
    version = invoke("--version")
    assert version.returncode == 0
    assert version.stdout.strip() == __version__
    help_result = invoke("--help")
    assert help_result.returncode == 0
    assert all(command in help_result.stdout for command in ["init", "demo", "serve", "audit", "export"])


def test_cli_initialization_reopens_the_same_workspace(tmp_path):
    root = tmp_path / "my research"
    initialized = invoke("init", "--workspace", root)
    assert initialized.returncode == 0, initialized.stderr
    workspace = Workspace(root)
    assert workspace.list_records() == []
    note = workspace.create_record("note", "Original question", "Question with µm units")
    reopened = invoke("init", "--workspace", root)
    assert reopened.returncode == 0, reopened.stderr
    assert Workspace(root).list_records() == [note]


@pytest.mark.parametrize("domain", ["microscopy", "environment"])
def test_cli_fictional_examples_audit_and_export(tmp_path, domain):
    root = tmp_path / domain
    demo = invoke("demo", "--workspace", root, "--domain", domain)
    assert demo.returncode == 0, demo.stderr
    assert "fictional" in demo.stdout
    workspace = Workspace(root)
    original = workspace.list_records()
    assert len(original) >= 8
    assert all(record["metadata"]["synthetic"] is True for record in original)
    assert any(("water sensor" if domain == "environment" else "fluorescence") in record["title"] for record in original)
    audit = invoke("audit", "--workspace", root)
    assert audit.returncode == 0, audit.stderr
    assert json.loads(audit.stdout)["integrity"] == []
    exported = invoke("export", "--workspace", root)
    assert exported.returncode == 0, exported.stderr
    bundle = json.loads(exported.stdout)
    assert bundle["records"] == original
    assert bundle["schema_version"] == 1
    markdown = invoke("export", "--workspace", root, "--format", "markdown")
    assert markdown.returncode == 0, markdown.stderr
    assert "Scientist OS research handoff" in markdown.stdout
    assert original[0]["id"] in markdown.stdout
    assert Workspace(root).list_records() == original


def test_cli_refuses_to_mix_demo_into_existing_research(tmp_path):
    root = tmp_path / "research"
    original = Workspace(root).create_record("note", "Private real research", "Do not mix synthetic data")
    result = invoke("demo", "--workspace", root)
    assert result.returncode == 2
    assert "empty workspace" in result.stderr
    assert "Traceback" not in result.stderr
    assert Workspace(root).list_records() == [original]


def test_cli_serve_binds_only_loopback_and_uses_requested_port(tmp_path, monkeypatch, capsys):
    import uvicorn

    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kwargs: calls.append((app, kwargs)))
    assert main(["serve", "--workspace", str(tmp_path / "served"), "--port", "8912"]) == 0
    assert len(calls) == 1
    assert calls[0][1]["host"] == "127.0.0.1"
    assert calls[0][1]["port"] == 8912
    assert "http://127.0.0.1:8912" in capsys.readouterr().out


@pytest.mark.parametrize("port", ["0", "80", "65536", "-1"])
def test_cli_bad_port_fails_before_initializing_workspace(tmp_path, port):
    root = tmp_path / "not-created"
    result = invoke("serve", "--workspace", root, "--port", port)
    assert result.returncode == 2
    assert "1024" in result.stderr
    assert "Traceback" not in result.stderr
    assert not root.exists()


def test_cli_bad_domain_does_not_initialize_workspace(tmp_path):
    root = tmp_path / "not-created"
    result = invoke("demo", "--workspace", root, "--domain", "unknown")
    assert result.returncode == 2
    assert not root.exists()


def test_cli_reports_unusable_workspace_path_without_a_traceback(tmp_path):
    root = tmp_path / "a-file"
    root.write_text("Keep this file", encoding="utf-8")
    result = invoke("init", "--workspace", root)
    assert result.returncode == 2, result.stderr
    assert "Error:" in result.stderr
    assert "Traceback" not in result.stderr
    assert root.read_text(encoding="utf-8") == "Keep this file"


def test_cli_reports_unsupported_schema_without_mutation(tmp_path):
    root = tmp_path / "workspace"
    workspace = Workspace(root)
    with sqlite3.connect(workspace.db_path) as connection:
        connection.execute("PRAGMA user_version = 999")
    result = invoke("init", "--workspace", root)
    assert result.returncode == 2
    assert "Unsupported workspace schema" in result.stderr
    assert "Traceback" not in result.stderr
    with sqlite3.connect(workspace.db_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 999


def test_cli_integrity_audit_exits_nonzero_for_stale_evidence(tmp_path):
    root = tmp_path / "workspace"
    workspace = Workspace(root)
    source = workspace.create_record("source", "Source", "Old source.")
    workspace.create_record("claim", "Claim", metadata={"citations": [{
        "record_id": source["id"], "quote": source["content"], "sha256": source["sha256"],
    }]})
    workspace.update_record(source["id"], expected_revision=1, content="Corrected source.")
    result = invoke("audit", "--workspace", root)
    assert result.returncode == 1, result.stderr
    codes = {finding["code"] for finding in json.loads(result.stdout)["integrity"]}
    assert {"citation_hash_mismatch", "citation_quote_mismatch"} <= codes
