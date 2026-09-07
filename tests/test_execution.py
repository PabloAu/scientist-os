"""Actual subprocess/repository/replay tests with invented arithmetic fixtures."""

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from scientist_os import execution
from scientist_os.execution import recover_run, replay_run, run_python, verify_run
from scientist_os.workspace import Workspace


PIPELINE = '''import argparse, json
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("--scientist-os-request")
r = json.loads(Path(p.parse_args().scientist_os_request).read_text(encoding="utf-8"))
values = [float(x) for x in Path(r["inputs"][0]["path"]).read_text().splitlines()]
out = Path(r["output_dir"])
(out / "result.json").write_text(json.dumps({"sum": sum(values), "config": r["config"]}))
(out / "qc.json").write_text(json.dumps({"passed": True, "n": len(values)}))
print("Executed selected Python on copied inputs")
'''


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                           text=True).stdout.strip()


@pytest.fixture
def fixture(tmp_path):
    repo = tmp_path / "versioned code with spaces"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "Synthetic software test")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "calculate.py").write_text(PIPELINE, encoding="utf-8")
    (repo / "requirements.txt").write_text("# standard library fixture\n")
    git(repo, "add", "calculate.py", "requirements.txt")
    git(repo, "commit", "-m", "Original fictional executable test fixture")
    data = tmp_path / "explicit numbers.txt"
    data.write_text("1\n2\n3\n")
    workspace = Workspace(tmp_path / "research project")
    record = workspace.create_record("dataset", "Fictional numbers", data.read_text(),
                                      metadata={"attachment_sha256": hashlib.sha256(data.read_bytes()).hexdigest()})
    spec = {"repo_path": str(repo), "revision": git(repo, "rev-parse", "HEAD"),
            "script": "calculate.py", "inputs": [{"path": str(data), "record_id": record["id"],
                                                     "locator": "Original fictional text file", "selection": "All three numbers"}],
            "permitted_roots": [str(tmp_path)], "trusted_code": True, "synthetic": True,
            "config": {"purpose": "arithmetic"}, "timeout_seconds": 10,
            "scientific": {"purpose": "Sum three fictional numbers", "estimand": "Sum",
                           "plan": "Read exactly the selected inputs", "units": "arbitrary units",
                           "independence_unit": "not inferential", "hierarchy": "one file; three fixed numbers",
                           "exclusions": [], "missingness": "none", "uncertainty": "none",
                           "qc": "Three input values", "limitations": "No scientific claim",
                           "decisions": [{"actor": "development test", "statement": "Execute fictional arithmetic",
                                          "basis": "user-authorized synthetic engineering test"}]}}
    return workspace, spec, repo, data


def test_executes_committed_python_records_preflight_and_replays(fixture):
    workspace, spec, repo, data = fixture
    # A dirty script must never sneak into execution of a selected commit.
    (repo / "calculate.py").write_text("raise RuntimeError('dirty code must not execute')")
    result = run_python(workspace, spec)
    run = result["run"]
    root = Path(result["run_directory"])
    assert run["status"] == "completed"
    assert json.loads((root / "outputs" / "result.json").read_text())["sum"] == 6
    preflight = workspace.get_run(run["preflight_id"])
    assert preflight["software"]["commit"] == spec["revision"]
    assert preflight["software"]["working_tree_status"]
    assert preflight["software"]["executed_dirty_worktree"] is False
    assert "requirements.txt" in preflight["software"]["lock_files"]
    assert preflight["environment"]["packages"]
    assert result["analysis"]["metadata"]["input_revisions"]
    assert result["analysis"]["review_status"] == "unreviewed"
    assert verify_run(workspace, run["id"])["intact"]
    replay = replay_run(workspace, run["id"])
    assert replay["comparison"]["equivalent"]
    assert replay["run"]["id"] != run["id"]
    assert data.read_text() == "1\n2\n3\n"


def test_changed_original_data_is_not_retroactively_substituted(fixture):
    workspace, spec, _, data = fixture
    first = run_python(workspace, spec)
    data.write_text("100\n200\n300\n")
    check = verify_run(workspace, first["run"]["id"])
    assert check["intact"] and check["current_source_changes"] == [str(data)]
    replay = replay_run(workspace, first["run"]["id"])
    assert replay["comparison"]["equivalent"]
    assert replay["analysis"] is None  # Historical result cannot masquerade as current data.
    with pytest.raises(ValueError, match="attachment hash"):
        run_python(workspace, spec)


@pytest.mark.parametrize("target", ["outputs/result.json", "inputs/000_explicit numbers.txt", "code/calculate.py", "config.json", "request.json"])
def test_tampered_inputs_code_configuration_or_outputs_block_replay(fixture, target):
    workspace, spec, _, _ = fixture
    result = run_python(workspace, spec)
    (Path(result["run_directory"]) / target).write_text("tampered")
    check = verify_run(workspace, result["run"]["id"])
    assert not check["intact"]
    with pytest.raises(RuntimeError, match="bytes changed"):
        replay_run(workspace, result["run"]["id"])


def test_execution_scope_revision_and_trust_are_explicit(fixture, tmp_path):
    workspace, spec, _, _ = fixture
    with pytest.raises(ValueError, match="trusted_code"):
        run_python(workspace, {**spec, "trusted_code": False})
    with pytest.raises(ValueError, match="immutable"):
        run_python(workspace, {**spec, "revision": "HEAD"})
    with pytest.raises(ValueError, match="outside"):
        run_python(workspace, {**spec, "permitted_roots": [str(workspace.root)]})
    with pytest.raises(ValueError, match="boundary"):
        run_python(workspace, {**spec, "script": "../calculate.py"})
    with pytest.raises(ValueError, match="same input"):
        run_python(workspace, {**spec, "inputs": spec["inputs"] * 2})
    with pytest.raises(ValueError, match="credentials"):
        run_python(workspace, {**spec, "config": {"api_key": "keep-this-out"}})


def change_pipeline(repo, spec, text):
    (repo / "calculate.py").write_text(text, encoding="utf-8")
    git(repo, "add", "calculate.py")
    git(repo, "commit", "-m", "Changed fictional test behavior")
    return {**spec, "revision": git(repo, "rev-parse", "HEAD")}


def test_failed_and_timed_out_code_retains_preflight_and_logs(fixture):
    workspace, spec, repo, _ = fixture
    broken = change_pipeline(repo, spec, "print('starting actual code', flush=True)\nraise ValueError('failed arithmetic')\n")
    failed = run_python(workspace, broken)
    assert failed["run"]["status"] == "failed" and failed["analysis"] is None
    assert "failed arithmetic" in (Path(failed["run_directory"]) / "stderr.log").read_text()
    assert verify_run(workspace, failed["run"]["id"])["intact"]
    slow = change_pipeline(repo, spec, "import time\nprint('started', flush=True)\ntime.sleep(20)\n")
    interrupted = run_python(workspace, {**slow, "timeout_seconds": .2})
    assert interrupted["run"]["status"] == "interrupted"
    assert "timeout" in interrupted["run"]["error"]
    assert workspace.get_run(interrupted["run"]["preflight_id"])["status"] == "prepared"


def test_qc_failure_retains_outputs_without_a_current_analysis(fixture):
    workspace, spec, repo, _ = fixture
    negative = change_pipeline(repo, spec, PIPELINE.replace('"passed": True', '"passed": False'))
    result = run_python(workspace, negative)
    assert result["run"]["status"] == "qc_failed"
    assert result["analysis"] is None and result["run"]["outputs"]
    with pytest.raises(ValueError, match="Only a completed"):
        replay_run(workspace, result["run"]["id"])


def test_abandoned_preflight_can_be_closed_without_reexecuting(fixture, monkeypatch):
    workspace, spec, _, _ = fixture
    monkeypatch.setattr(execution, "_execute", lambda workspace, preflight, root: preflight)
    preflight = run_python(workspace, spec)
    assert verify_run(workspace, preflight["id"])["status"] == "unfinished"
    recovered = recover_run(workspace, preflight["id"], "Test host stopped before launching code")
    assert recovered["run"]["status"] == "interrupted"
    assert recovered["run"]["outputs"] == {}
    assert recover_run(workspace, preflight["id"], "Already closed")["already_finished"]


def test_replay_declared_numeric_tolerance_does_not_hide_text_changes(fixture):
    workspace, spec, repo, _ = fixture
    code = PIPELINE.replace('{"sum": sum(values), "config": r["config"]}',
                            '{"sum": sum(values) + int(out.parent.name[-1], 16)*1e-9, "units": "nm"}')
    modified = change_pipeline(repo, spec, code)
    result = run_python(workspace, {**modified, "replay": {"mode": "numeric_json", "atol": 2e-8, "rtol": 0}})
    assert replay_run(workspace, result["run"]["id"])["comparison"]["equivalent"]
    assert not execution._equivalent({"value": 1, "units": "nm"}, {"value": 1.000001, "units": "um"}, atol=.1, rtol=0)
    assert not execution._equivalent({"passed": True}, {"passed": 1}, atol=1, rtol=1)


def test_child_does_not_inherit_host_credentials(fixture, monkeypatch):
    workspace, spec, repo, _ = fixture
    monkeypatch.setenv("SCIENTIST_OS_TEST_SECRET", "private")
    code = PIPELINE + "\nimport os\nassert 'SCIENTIST_OS_TEST_SECRET' not in os.environ\n"
    modified = change_pipeline(repo, spec, code)
    assert run_python(workspace, modified)["run"]["status"] == "completed"


def test_module_collision_cannot_execute_environment_entry_point(fixture):
    workspace, spec, repo, _ = fixture
    (repo / "json").mkdir()
    (repo / "json" / "tool.py").write_text(PIPELINE, encoding="utf-8")
    git(repo, "add", "json/tool.py")
    git(repo, "commit", "-m", "Fictional namespace collision fixture")
    module_spec = {key: value for key, value in spec.items() if key != "script"}
    module_spec.update(module="json.tool", revision=git(repo, "rev-parse", "HEAD"))
    result = run_python(workspace, module_spec)
    assert result["run"]["status"] == "failed" and result["analysis"] is None
    stderr = (Path(result["run_directory"]) / "stderr.log").read_text()
    assert "outside the committed code snapshot" in stderr
    assert "unrecognized arguments" not in stderr  # The standard-library entry point never ran.
    assert not result["run"]["outputs"]


@pytest.mark.parametrize("entry", ["fictional_pipeline.calculate", "fictional_pipeline"])
def test_committed_namespace_module_and_package_replay(fixture, entry):
    workspace, spec, repo, _ = fixture
    package = repo / "fictional_pipeline"
    package.mkdir()
    filename = "calculate.py" if "." in entry else "__main__.py"
    (package / filename).write_text(PIPELINE, encoding="utf-8")
    git(repo, "add", "fictional_pipeline")
    git(repo, "commit", "-m", "Fictional committed module fixture")
    module_spec = {key: value for key, value in spec.items() if key != "script"}
    module_spec.update(module=entry, revision=git(repo, "rev-parse", "HEAD"))
    result = run_python(workspace, module_spec)
    assert result["run"]["status"] == "completed"
    assert replay_run(workspace, result["run"]["id"])["comparison"]["equivalent"]
