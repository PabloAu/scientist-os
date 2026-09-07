"""Recorded execution of explicitly trusted Python at an immutable Git revision.

This is an execution journal, not an OS sandbox. The host must authorize the
code and filesystem scope. Child code has the operating-system user's rights.
No dependency installation, fetch, push, network request or paid work occurs here.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import signal
import subprocess
import sys
import tarfile
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from .workspace import Workspace, _bounded_json, _now, _redact


_COMMIT = re.compile(r"(?:[a-fA-F0-9]{40}|[a-fA-F0-9]{64})\Z")
_MODULE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\Z")
_SCIENCE = ("purpose", "estimand", "plan", "units", "independence_unit", "hierarchy",
            "exclusions", "missingness", "uncertainty", "qc", "limitations", "decisions")
_LOCKS = {"uv.lock", "poetry.lock", "Pipfile.lock", "requirements.txt", "pyproject.toml",
          "environment.yml", "conda-lock.yml"}
_BOOTSTRAP = '''import importlib.util, json, pathlib, random, runpy, sys
request_path = pathlib.Path(sys.argv[1]).resolve()
request = json.loads(request_path.read_text(encoding="utf-8"))
root = pathlib.Path(request["code_dir"])
sys.path[:0] = [str(root / "src"), str(root)]
random.seed(request["seed"])
entry = request["entry"]
sys.argv = [entry.get("script", entry.get("module")), "--scientist-os-request", str(request_path)]
if "script" in entry:
    runpy.run_path(str(root / entry["script"]), run_name="__main__")
else:
    executable_module = entry["module"]
    module_spec = importlib.util.find_spec(executable_module)
    if module_spec is not None and module_spec.submodule_search_locations is not None:
        executable_module += ".__main__"
        module_spec = importlib.util.find_spec(executable_module)
    if (module_spec is None or not module_spec.origin
            or not pathlib.Path(module_spec.origin).resolve().is_relative_to(root.resolve())):
        raise RuntimeError("Resolved module entry point is outside the committed code snapshot")
    runpy.run_module(executable_module, run_name="__main__", alter_sys=True)
'''


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path, value: object) -> None:
    data = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(data + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def _relative(value: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("Use a nonempty relative POSIX path without drive letters")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"..", ".git", ".upstream"} for part in path.parts):
        raise ValueError("Path leaves the selected source boundary or names a private source")
    if str(path) in {".", ""}:
        raise ValueError("A file path is required")
    return Path(*path.parts)


def _permitted(value: str, roots: list[Path], *, directory: bool = False) -> Path:
    raw = Path(value).expanduser().absolute()
    path = raw.resolve(strict=True)
    if ".upstream" in {p.lower() for p in raw.parts + path.parts}:
        raise ValueError("Preserved private source checkouts cannot be executed or imported here")
    if not any(path.is_relative_to(root) for root in roots):
        raise ValueError(f"Path is outside the explicit permitted roots: {path}")
    if any(p.is_symlink() or p.is_junction() for p in [raw, *raw.parents]):
        raise ValueError("Symlink/junction source paths are unsupported; select a physical source")
    if directory != path.is_dir() or (not directory and not path.is_file()):
        raise ValueError("Select a regular file or repository directory as appropriate")
    return path


def _git(repo: Path, *arguments: str, required: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(repo), *arguments], capture_output=True,
                            timeout=30, check=False, shell=False,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if required and result.returncode:
        raise ValueError("Git operation failed: " + result.stderr.decode("utf-8", "replace")[:1000])
    return result.stdout.decode("utf-8", "replace").strip() if not result.returncode else ""


def _safe_origin(origin: str) -> str:
    # Remote URL credentials are never necessary to identify software provenance.
    if "://" in origin:
        parsed = urlsplit(origin)
        host = parsed.hostname or ""
        if parsed.port:
            host += f":{parsed.port}"
        return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    return _redact(origin)


def _files(root: Path, *, limit: int = 20_000) -> dict[str, dict]:
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise ValueError("Symlinks/junctions are not allowed in run snapshots or outputs")
        if path.is_file():
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError("A run file escaped its root")
            result[path.relative_to(root).as_posix()] = {"sha256": _sha(path),
                                                        "bytes": path.stat().st_size}
            if len(result) > limit:
                raise ValueError("Run file count exceeds the bounded snapshot limit")
    return result


def _run_directory(workspace: Workspace, execution_id: str) -> Path:
    root = workspace.root / "runs" / execution_id
    if not root.resolve().is_relative_to(workspace.root):
        raise ValueError("Run directory leaves the workspace")
    if any(path.is_symlink() or path.is_junction() for path in (root, root.parent)):
        raise ValueError("Run directories cannot be symlinks or junctions")
    return root


def _environment() -> dict:
    packages = sorted({(distribution.metadata.get("Name", "unknown"), distribution.version)
                       for distribution in importlib.metadata.distributions()})
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "executable": sys.executable, "executable_sha256": _sha(Path(sys.executable)),
            "platform": platform.platform(), "machine": platform.machine(),
            "packages": [{"name": name, "version": version} for name, version in packages],
            "environment_values": "Only a small OS/runtime allowlist is passed; secrets are omitted.",
            "runner_sha256": _sha(Path(__file__)),
            "science_sha256": _sha(Path(__file__).with_name("science.py"))}


def _child_environment(seed: int, run_dir: Path) -> dict[str, str]:
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "LANG", "LC_ALL", "TZ"}
    environment = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    temporary = run_dir / "temporary"
    temporary.mkdir(exist_ok=True)
    environment.update({"TEMP": str(temporary), "TMP": str(temporary), "TMPDIR": str(temporary),
                        "PYTHONHASHSEED": str(seed), "PYTHONDONTWRITEBYTECODE": "1",
                        "PYTHONIOENCODING": "utf-8", "MPLCONFIGDIR": str(temporary / "matplotlib")})
    return environment


def _validate_spec(spec: dict) -> dict:
    clean = _bounded_json(spec, "analysis execution specification", 256 * 1024)
    if clean.get("trusted_code") is not True:
        raise ValueError("Explicit trusted_code=true is required; this runner is not a sandbox")
    if clean != _redact(clean):
        raise ValueError("Do not include credentials in execution specifications")
    if not isinstance(clean.get("permitted_roots"), list) or not clean["permitted_roots"]:
        raise ValueError("Explicit permitted_roots are required")
    if bool(clean.get("script")) == bool(clean.get("module")):
        raise ValueError("Select exactly one script or module")
    if clean.get("script"):
        script = _relative(clean["script"])
        if script.suffix.lower() != ".py":
            raise ValueError("The selected script must be Python")
    elif not _MODULE.fullmatch(clean["module"]):
        raise ValueError("Module must be a dotted Python name")
    if not _COMMIT.fullmatch(clean.get("revision", "")):
        raise ValueError("revision must be a full immutable Git commit, never 'latest' or HEAD")
    scientific = clean.get("scientific", {})
    if not isinstance(scientific, dict) or any(key not in scientific for key in _SCIENCE):
        raise ValueError("Record scientific purpose, estimand, plan, units, hierarchy, QC and decisions")
    for key in ("purpose", "estimand", "plan", "units", "independence_unit", "hierarchy"):
        if not isinstance(scientific[key], str) or not scientific[key].strip():
            raise ValueError(f"scientific.{key} must be an explicit nonempty declaration")
    if not isinstance(scientific["decisions"], list) or not scientific["decisions"]:
        raise ValueError("Record attributed scientific decisions or fixture authorization")
    for decision in scientific["decisions"]:
        if not isinstance(decision, dict) or not all(decision.get(k) for k in ("actor", "statement", "basis")):
            raise ValueError("Every decision needs actor, statement and basis; never invent human approval")
    if not isinstance(clean.get("inputs"), list) or not 1 <= len(clean["inputs"]) <= 128:
        raise ValueError("Select 1–128 explicit input files")
    for item in clean["inputs"]:
        if not isinstance(item, dict) or not all(item.get(k) for k in ("path", "locator", "selection")):
            raise ValueError("Each input needs path, original locator and selection criteria")
    if not isinstance(clean.get("config", {}), dict):
        raise ValueError("config must be a JSON object")
    clean.setdefault("config", {})
    clean.setdefault("seed", 0)
    if type(clean["seed"]) is not int or not 0 <= clean["seed"] < 2**32:
        raise ValueError("seed must be an integer between 0 and 2**32-1")
    clean.setdefault("timeout_seconds", 300)
    if type(clean["timeout_seconds"]) not in {int, float} or not 0 < clean["timeout_seconds"] <= 86_400:
        raise ValueError("timeout_seconds must be positive and at most one day")
    clean.setdefault("replay", {"mode": "exact", "atol": 0, "rtol": 0})
    replay = clean["replay"]
    if not isinstance(replay, dict) or replay.get("mode") not in {"exact", "numeric_json"}:
        raise ValueError("Declare replay mode exact or numeric_json before execution")
    for key in ("atol", "rtol"):
        replay.setdefault(key, 0)
        if type(replay[key]) not in {int, float} or not math.isfinite(replay[key]) or replay[key] < 0:
            raise ValueError("Replay tolerances must be finite nonnegative numbers")
    return clean


def _snapshot_code(repo: Path, commit: str, root: Path) -> dict:
    if Path(_git(repo, "rev-parse", "--show-toplevel")).resolve() != repo:
        raise ValueError("repo_path must be the owning repository root")
    if _git(repo, "rev-parse", "--verify", commit + "^{commit}").lower() != commit.lower():
        raise ValueError("revision must identify a commit")
    root.mkdir()
    archive = root.parent / "software.tar"
    _git(repo, "archive", "--format=tar", "--output=" + str(archive), commit)
    if archive.stat().st_size > 256 * 1024 * 1024:
        raise ValueError("Code snapshot exceeds 256 MiB; separate code from datasets")
    with tarfile.open(archive) as packed:
        members = packed.getmembers()
        if len(members) > 20_000:
            raise ValueError("Software snapshot exceeds 20,000 members")
        for member in members:
            relative = _relative(member.name.rstrip("/"))
            target = root / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                with packed.extractfile(member) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
            else:
                raise ValueError("Git symlinks, devices and submodule contents are unsupported")
    # Submodule content is absent from archive: refuse to imply a complete code snapshot.
    tree = _git(repo, "ls-tree", "-r", commit)
    if any(line.startswith("160000 ") for line in tree.splitlines()):
        raise ValueError("Pin and vendor submodule code explicitly before execution")
    patch = subprocess.run(["git", "-C", str(repo), "diff", "--binary", "HEAD"],
                           capture_output=True, check=True, timeout=30, shell=False,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0).stdout
    # Preserve patch identity without leaking credential-shaped text into an otherwise safe journal.
    patch_text = patch.decode("utf-8", "replace")
    safe_patch = _redact(patch_text)
    patch_path = root.parent / "working-tree.patch"
    patch_path.write_text(safe_patch, encoding="utf-8", newline="\n")
    files = _files(root)
    remote_branches = _git(repo, "for-each-ref", "--contains=" + commit,
                           "--format=%(refname)", "refs/remotes/").splitlines()
    return {"repository": str(repo), "commit": commit.lower(),
            "head_at_launch": _git(repo, "rev-parse", "HEAD"),
            "tree": _git(repo, "rev-parse", commit + "^{tree}"),
            "origin": _safe_origin(_git(repo, "remote", "get-url", "origin", required=False)),
            "working_tree_status": _redact(_git(repo, "status", "--porcelain=v1")),
            "working_tree_patch_sha256": hashlib.sha256(patch).hexdigest(),
            "patch_redacted": patch_text != safe_patch,
            "executed_dirty_worktree": False,
            "push_verification": {"status": "cached_remote_contains" if remote_branches else "unverified",
                                  "cached_remote_refs": remote_branches,
                                  "live_remote_checked": False,
                                  "note": "Local tracking refs may be stale. Host must verify live GitHub revision before release."},
            "archive_sha256": _sha(archive), "files": files,
            "lock_files": {name: item for name, item in files.items() if Path(name).name in _LOCKS}}


def _load_execution(workspace: Workspace, run_id: str) -> tuple[dict, dict | None, Path]:
    # Accept either the final execution id or its immutable preflight journal id.
    runs = workspace.list_runs()
    preflight = next((run for run in runs if run.get("type") == "python_execution_preflight"
                      and run_id in {run["id"], run.get("execution_id")}), None)
    if preflight is None:
        raise KeyError(run_id)
    execution_id = preflight["execution_id"]
    outcome = next((run for run in runs if run["id"] == execution_id), None)
    root = _run_directory(workspace, execution_id)
    if not root.resolve().is_relative_to(workspace.root) or root.is_symlink() or root.is_junction():
        raise ValueError("Execution directory escaped the workspace")
    return preflight, outcome, root


def _check_inventory(root: Path, expected: dict[str, dict], *, label: str) -> list[str]:
    try:
        actual = _files(root)
    except (ValueError, OSError) as exc:
        return [f"{label}: {exc}"]
    return [f"{label}: {name} changed, missing or unexpected"
            for name in sorted(set(expected) | set(actual)) if expected.get(name) != actual.get(name)]


def verify_run(workspace: Workspace, run_id: str) -> dict:
    """Verify recorded bytes against the journal; source changes do not rewrite history."""
    preflight, outcome, root = _load_execution(workspace, run_id)
    failures = []
    for name, item in preflight["manifest_files"].items():
        path = root / _relative(name)
        if not path.is_file() or path.is_symlink() or _sha(path) != item["sha256"]:
            failures.append(f"manifest: {name} changed or missing")
    failures += _check_inventory(root / "code", preflight["software"]["files"], label="code")
    expected_inputs = {item["snapshot"]: {"sha256": item["sha256"], "bytes": item["bytes"]}
                       for item in preflight["inputs"]}
    failures += _check_inventory(root / "inputs", expected_inputs, label="input")
    source_changes = []
    for item in preflight["inputs"]:
        source = Path(item["original_path"])
        if not source.is_file() or _sha(source) != item["sha256"]:
            source_changes.append(item["original_path"])
        if item.get("record_id"):
            try:
                record = workspace.get_record(item["record_id"])
                if record["revision"] != item["record_revision"]:
                    source_changes.append(item["record_id"])
            except KeyError:
                source_changes.append(item["record_id"])
    if outcome:
        failures += _check_inventory(root / "outputs", outcome.get("outputs", {}), label="output")
        for name, item in outcome.get("final_files", {}).items():
            path = root / _relative(name)
            if not path.is_file() or path.is_symlink() or _sha(path) != item["sha256"]:
                failures.append(f"final: {name} changed or missing")
    return {"run_id": preflight["execution_id"], "intact": not failures,
            "status": outcome["status"] if outcome else "unfinished",
            "failures": failures, "current_source_changes": sorted(set(source_changes)),
            "historical_snapshot_replayable": not failures,
            "note": "Hash verification is local tamper evidence, not adversarial attestation or scientific approval."}


def _stop(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       capture_output=True, timeout=15, check=False,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _finish(workspace: Workspace, preflight: dict, root: Path, status: str,
            *, error: str = "", returncode: int | None = None) -> dict:
    try:
        outputs = _files(root / "outputs")
    except (OSError, ValueError) as exc:
        outputs = {}
        status, error = "failed", str(exc)
    integrity = verify_run(workspace, preflight["execution_id"])
    if not integrity["intact"]:
        status = "failed"
        error = "; ".join(integrity["failures"])
    # Never promote a zero-exit process with no artifact, or with failed declared QC.
    qc = None
    qc_file = root / "outputs" / "qc.json"
    if status == "completed":
        if not outputs:
            status, error = "failed", "Pipeline produced no output files"
        elif qc_file.is_file():
            try:
                qc = json.loads(qc_file.read_text(encoding="utf-8"))
                if not isinstance(qc, dict) or type(qc.get("passed")) is not bool:
                    raise ValueError("qc.json requires a boolean passed and check details")
                if not qc["passed"]:
                    status = "qc_failed"
            except (ValueError, UnicodeError) as exc:
                status, error = "failed", str(exc)
    logs = {}
    for name in ("stdout.log", "stderr.log"):
        path = root / name
        if path.is_symlink() or path.is_junction():
            status, error = "failed", "Execution log was replaced by a link; original target was not read or changed"
            continue
        if path.exists():
            # These text logs deliberately retain redacted text, never credential-shaped tokens.
            before = path.read_text(encoding="utf-8", errors="replace")
            after = _redact(before)
            if after != before:
                path.write_text(after, encoding="utf-8", newline="\n")
            logs[name] = {"sha256": _sha(path), "bytes": path.stat().st_size,
                          "redacted": before != after}
    final = {"id": preflight["execution_id"], "type": "python_execution",
             "preflight_id": preflight["id"], "created_at": preflight["created_at"],
             "finished_at": _now(), "status": status, "returncode": returncode,
             "error": _redact(error), "outputs": outputs, "logs": logs, "qc": qc,
             "current_source_changes": integrity["current_source_changes"],
             "manifest_path": str(root / "final.json"), "scientific_approval": False,
             "replay_of": preflight.get("replay_of")}
    _json(root / "final.json", final)
    final["final_files"] = {"final.json": {"sha256": _sha(root / "final.json")}, **logs}
    final = workspace.save_run(final)
    _json(root / "active.json", {"status": status, "run_id": final["id"], "finished_at": final["finished_at"]})
    analysis = None
    if status == "completed" and not integrity["current_source_changes"]:
        inputs = [item for item in preflight["inputs"] if item.get("record_id")]
        links = list(dict.fromkeys(item["record_id"] for item in inputs))
        metadata = {"execution_run_id": final["id"], "manifest_path": final["manifest_path"],
                    "code_commit": preflight["software"]["commit"],
                    "input_revisions": {item["record_id"]: item["record_revision"] for item in inputs},
                    "input_hashes": {item["record_id"]: item["sha256"] for item in inputs},
                    "units": preflight["spec"]["scientific"]["units"],
                    "independence_unit": preflight["spec"]["scientific"]["independence_unit"],
                    "synthetic": preflight["spec"].get("synthetic", False), "external_allowed": False,
                    "outputs": outputs, "scientific": preflight["spec"]["scientific"]}
        try:
            analysis = workspace.create_record("analysis", preflight["spec"]["scientific"]["purpose"],
                                               json.dumps(final, indent=2), metadata=metadata, links=links)
        except (RuntimeError, ValueError) as exc:
            # A concurrent source edit cannot invalidate the already completed execution journal.
            return {"run": final, "analysis": None, "registration_error": str(exc),
                    "run_directory": str(root)}
    return {"run": final, "analysis": analysis, "run_directory": str(root)}


def _execute(workspace: Workspace, preflight: dict, root: Path) -> dict:
    command = [sys.executable, "-s", str(root / "bootstrap.py"), str(root / "request.json")]
    process = None
    status, error, returncode = "failed", "", None
    _json(root / "active.json", {"status": "launching", "run_id": preflight["execution_id"],
                                "owner_pid": os.getpid(), "started_at": _now()})
    try:
        with (root / "stdout.log").open("wb") as stdout, (root / "stderr.log").open("wb") as stderr:
            process = subprocess.Popen(command, cwd=root / "code", stdout=stdout, stderr=stderr,
                                       stdin=subprocess.DEVNULL, shell=False,
                                       env=_child_environment(preflight["spec"]["seed"], root),
                                       start_new_session=os.name != "nt",
                                       creationflags=(subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
                                       if os.name == "nt" else 0)
            _json(root / "active.json", {"status": "running", "run_id": preflight["execution_id"],
                                        "owner_pid": os.getpid(), "child_pid": process.pid,
                                        "started_at": _now()})
            returncode = process.wait(timeout=preflight["spec"]["timeout_seconds"])
            status = "completed" if returncode == 0 else "failed"
            if returncode:
                error = f"Python exited with status {returncode}; inspect stderr.log"
    except subprocess.TimeoutExpired:
        status, error = "interrupted", "Execution exceeded its declared timeout; partial artifacts retained"
    except (KeyboardInterrupt, SystemExit):
        status, error = "interrupted", "Host execution interrupted; partial artifacts retained"
    except OSError as exc:
        error = str(exc)
    finally:
        if process is not None and process.poll() is None:
            _stop(process)
    return _finish(workspace, preflight, root, status, error=error, returncode=returncode)


def run_python(workspace: Workspace, spec: dict) -> dict:
    """Snapshot exact selected data/code, persist the plan, execute, and link output.

    The script/module receives --scientist-os-request PATH. The request contains
    copied inputs, config, seed and output_dir. It must write its artifacts there.
    """
    spec = _validate_spec(spec)
    roots = [Path(path).expanduser().resolve(strict=True) for path in spec["permitted_roots"]]
    repo = _permitted(spec["repo_path"], roots, directory=True)
    selected = [_permitted(item["path"], roots) for item in spec["inputs"]]
    if len(set(selected)) != len(selected):
        raise ValueError("The same input file was selected more than once")
    execution_id = "run_" + uuid4().hex
    root = _run_directory(workspace, execution_id)
    root.mkdir(parents=True)
    for name in ("inputs", "outputs"):
        (root / name).mkdir()
    software = _snapshot_code(repo, spec["revision"], root / "code")
    entry = {key: spec[key] for key in ("script", "module") if spec.get(key)}
    if "script" in entry and not (root / "code" / _relative(entry["script"])).is_file():
        raise ValueError("Selected script is absent from the committed snapshot")
    if "module" in entry:
        module = Path(*entry["module"].split("."))
        if not any((base / module.with_suffix(".py")).is_file() or
                   (base / module / "__main__.py").is_file()
                   for base in (root / "code", root / "code" / "src")):
            raise ValueError("Selected module must exist in the committed snapshot, not only the environment")
    inputs = []
    for index, (item, source) in enumerate(zip(spec["inputs"], selected, strict=True)):
        digest = _sha(source)
        destination = root / "inputs" / f"{index:03d}_{source.name}"
        shutil.copyfile(source, destination)
        if _sha(destination) != digest or _sha(source) != digest:
            raise RuntimeError("Input changed during snapshot; repeat selection after reconciling its owner")
        snapshot = {"original_path": str(source), "locator": item["locator"],
                    "selection": item["selection"], "sha256": digest,
                    "bytes": destination.stat().st_size, "snapshot": destination.name}
        if item.get("record_id"):
            record = workspace.validate_current(item["record_id"])
            attachment_hash = record["metadata"].get("attachment_sha256")
            if attachment_hash and attachment_hash != digest:
                raise ValueError("Selected file does not match the registered original attachment hash")
            snapshot.update({"record_id": record["id"], "record_revision": record["revision"],
                             "record_content_sha256": record["sha256"]})
        inputs.append(snapshot)
    _json(root / "config.json", spec["config"])
    environment = _environment()
    _json(root / "environment.json", environment)
    request = {"schema_version": 1, "code_dir": str(root / "code"), "entry": entry,
               "inputs": [{"path": str(root / "inputs" / item["snapshot"]),
                           "sha256": item["sha256"], "locator": item["locator"]} for item in inputs],
               "config": spec["config"], "seed": spec["seed"], "output_dir": str(root / "outputs")}
    _json(root / "request.json", request)
    (root / "bootstrap.py").write_text(_BOOTSTRAP, encoding="utf-8", newline="\n")
    preflight = {"type": "python_execution_preflight", "execution_id": execution_id,
                 "created_at": _now(), "status": "prepared", "spec": spec, "inputs": inputs,
                 "software": software, "environment": environment, "replay_of": None,
                 "execution_command": [sys.executable, "-s", "bootstrap.py", "request.json"],
                 "no_network_requested": True,
                 "trust_boundary": "Authorized trusted Python, not a sandbox; no credentials inherited."}
    _json(root / "preflight.json", preflight)
    preflight["manifest_files"] = {name: {"sha256": _sha(root / name)} for name in
                                   ("preflight.json", "config.json", "environment.json", "request.json",
                                    "bootstrap.py", "software.tar", "working-tree.patch")}
    preflight = workspace.save_run(preflight)
    return _execute(workspace, preflight, root)


def _equivalent(before: object, after: object, *, atol: float, rtol: float) -> bool:
    if isinstance(before, bool) or isinstance(after, bool):
        return type(before) is type(after) and before == after
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        return math.isfinite(before) and math.isfinite(after) and math.isclose(before, after, abs_tol=atol, rel_tol=rtol)
    if isinstance(before, dict) and isinstance(after, dict):
        return before.keys() == after.keys() and all(_equivalent(before[key], after[key], atol=atol, rtol=rtol) for key in before)
    if isinstance(before, list) and isinstance(after, list):
        return len(before) == len(after) and all(_equivalent(a, b, atol=atol, rtol=rtol) for a, b in zip(before, after, strict=True))
    return type(before) is type(after) and before == after


def replay_run(workspace: Workspace, run_id: str) -> dict:
    """Run preserved snapshots in a new directory using the predeclared comparison."""
    preflight, original, source = _load_execution(workspace, run_id)
    verification = verify_run(workspace, run_id)
    if not verification["intact"]:
        raise RuntimeError("Replay refused: preserved run bytes changed: " + "; ".join(verification["failures"]))
    if not original or original["status"] != "completed":
        raise ValueError("Only a completed run can be replayed for equivalence; failed work needs a revised plan")
    environment = _environment()
    for key in ("python", "implementation", "executable_sha256", "packages", "runner_sha256", "science_sha256"):
        if environment[key] != preflight["environment"][key]:
            raise RuntimeError(f"Environment changed ({key}); restore the recorded environment before replay")
    execution_id = "run_" + uuid4().hex
    root = _run_directory(workspace, execution_id)
    root.mkdir()
    for name in ("code", "inputs"):
        shutil.copytree(source / name, root / name)
    (root / "outputs").mkdir()
    for name in preflight["manifest_files"]:
        shutil.copyfile(source / name, root / name)
    request = json.loads((root / "request.json").read_text(encoding="utf-8"))
    request["code_dir"], request["output_dir"] = str(root / "code"), str(root / "outputs")
    for item, snapshot in zip(request["inputs"], preflight["inputs"], strict=True):
        item["path"] = str(root / "inputs" / snapshot["snapshot"])
    _json(root / "request.json", request)
    replay = {key: value for key, value in preflight.items() if key not in {"id", "manifest_files"}}
    replay.update({"execution_id": execution_id, "created_at": _now(), "replay_of": original["id"]})
    _json(root / "preflight.json", replay)
    replay["manifest_files"] = {name: {"sha256": _sha(root / name)} for name in preflight["manifest_files"]}
    replay = workspace.save_run(replay)
    result = _execute(workspace, replay, root)
    criteria = preflight["spec"]["replay"]
    differences = []
    new_outputs = result["run"]["outputs"]
    for name in sorted(set(original["outputs"]) | set(new_outputs)):
        identical = original["outputs"].get(name) == new_outputs.get(name)
        if not identical and criteria["mode"] == "numeric_json" and name.endswith(".json") and name in original["outputs"] and name in new_outputs:
            try:
                identical = _equivalent(json.loads((source / "outputs" / name).read_text(encoding="utf-8")),
                                        json.loads((root / "outputs" / name).read_text(encoding="utf-8")),
                                        atol=criteria["atol"], rtol=criteria["rtol"])
            except (ValueError, UnicodeError):
                identical = False
        if not identical:
            differences.append(name)
    comparison = {"type": "python_replay_comparison", "original_run_id": original["id"],
                  "replay_run_id": result["run"]["id"], "criteria": criteria,
                  "equivalent": not differences and result["run"]["status"] == "completed",
                  "differences": differences, "current_source_changes": verification["current_source_changes"]}
    result["comparison"] = workspace.save_run(comparison)
    return result


def _pid_exists(pid: int) -> bool:
    if os.name == "nt":
        result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                                capture_output=True, timeout=10, check=True,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        return f'"{pid}"' in result.stdout.decode("utf-8", "replace")
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def recover_run(workspace: Workspace, run_id: str, note: str) -> dict:
    """Close an abandoned journal; never rerun external actions or auto-retry code."""
    preflight, outcome, root = _load_execution(workspace, run_id)
    if outcome:
        return {"run": outcome, "already_finished": True, "verification": verify_run(workspace, run_id)}
    if not isinstance(note, str) or not note.strip():
        raise ValueError("Record why this run is known to be abandoned")
    active_path = root / "active.json"
    if active_path.is_file():
        active = json.loads(active_path.read_text(encoding="utf-8"))
        for key in ("owner_pid", "child_pid"):
            if active.get(key) and _pid_exists(active[key]):
                raise RuntimeError("A recorded process is still active; stop it through its owning host first")
    return _finish(workspace, preflight, root, "interrupted", error="Recovered abandoned run: " + note)
