# Reproducible Python execution

The conversational host can inspect a permitted dataset, discuss its scientific
design, develop an ordinary Python pipeline, commit it in its owning repository,
and invoke `analysis.run`. This service actually starts Python. It is not a
fixed calculator menu or a proposal pretending that code ran.

The corresponding Python interface is:

```python
from scientist_os.execution import run_python, verify_run, replay_run, recover_run
from scientist_os.workspace import Workspace

workspace = Workspace("path/to/research-workspace")
result = run_python(workspace, specification)
verification = verify_run(workspace, result["run"]["id"])
replay = replay_run(workspace, result["run"]["id"])
```

All results are JSON-compatible. `run_python` returns `run`, `analysis` (a linked
unreviewed record or null), and `run_directory`. Replay adds an immutable
`comparison` run. The CLI/MCP host facade exposes these as `analysis.run`,
`analysis.verify`, `analysis.replay` and `analysis.recover`; use the facade's
operation schema to supply their arguments.

## Execution specification

```json
{
  "repo_path": "ABSOLUTE_PATH_TO_THE_OWNING_REPOSITORY",
  "revision": "FULL_40_OR_64_CHARACTER_GIT_COMMIT",
  "script": "examples/pipelines/summary_pipeline.py",
  "permitted_roots": ["ABSOLUTE_PERMITTED_CODE_ROOT", "ABSOLUTE_PERMITTED_DATA_ROOT"],
  "trusted_code": true,
  "synthetic": true,
  "inputs": [{
    "path": "ABSOLUTE_PATH_TO_SELECTED.csv",
    "record_id": "OPTIONAL_EXISTING_DATASET_RECORD_ID",
    "locator": "Original fictional fixture file",
    "selection": "All ten observations in six independent fictional preparations"
  }],
  "config": {
    "value_column": "residual_nm",
    "group_column": "condition",
    "unit_column": "preparation",
    "units": "nm",
    "figure_title": "Fictional phantom residuals by preparation",
    "minimum_independent_units": 3
  },
  "seed": 0,
  "timeout_seconds": 300,
  "replay": {"mode": "exact", "atol": 0, "rtol": 0},
  "scientific": {
    "purpose": "Summarize fictional phantom residuals by preparation",
    "estimand": "Mean of preparation means within each condition",
    "plan": "Equal-weight unit means, missingness accounting, unit-count QC and one SEM",
    "units": "nm",
    "independence_unit": "preparation",
    "hierarchy": "Technical observations nested in distinct preparations; groups are unpaired",
    "exclusions": [],
    "missingness": "Exclude and report only empty numeric cells; no imputation",
    "uncertainty": "One SEM across preparation means; not a confidence interval",
    "qc": "At least three nonmissing preparations per group",
    "limitations": "Fictional arithmetic exercise; no causal or biological inference",
    "decisions": [{
      "actor": "Development agent (fixture only)",
      "statement": "Run the predefined fictional exercise and exact replay",
      "basis": "The user's authorization to build and verify fictional examples"
    }]
  }
}
```

Remove `record_id` if the file has not been registered. When supplied, its
revision is frozen and linked; an existing `attachment_sha256` must match the
selected original bytes. File-byte hashes and record-content hashes are stored
separately because extraction/encoding may change the representation.

Use `module: "package.pipeline"` instead of `script` for a module located in
the committed root or its `src/` directory. Exactly one entry is required.
The entry must belong to the selected commit; a module found only in the
installed environment cannot masquerade as versioned pipeline source.

The scientific declarations are facts supplied or resolved with the scientist.
The host must not fill unknown independence, units or experimental history with
plausible guesses. A permission to run software is separate from a scientist's
approval of an estimand, eligibility decision, pooling or scientific claim.
Exploratory work remains exploratory; record the later freeze before confirmatory
test inspection. Existing task authorization covers routine reversible work.

## Pipeline interface

The chosen script/module receives `--scientist-os-request PATH`. That JSON file
contains `code_dir`, `entry`, `inputs` (copied file paths, original locators and
SHA-256 hashes), `config`, `seed` and `output_dir`. It must write artifacts to
`output_dir`. Paths in the request point to the run snapshots, not the original
source files. The runner uses the current installed Python and prepends the
committed code root and its `src/` directory to imports.

Ordinary scientific Python is supported: data loaders, model fitting, custom
plots, domain pipelines and result checks. The pipeline can emit a `qc.json`
object with a boolean `passed` and details of the checks. False produces a
retained `qc_failed` run and no current analysis record. No output after a zero
exit code is a failure. Absence of `qc.json` means the runner has **not** checked
scientific QC; the manifest still records the declared QC procedure. Host and
scientist inspect outputs and resolve assumptions before relying on claims.

The supplied `examples/pipelines/summary_pipeline.py` reuses the existing
independent-unit summary and SVG renderer. Its fixture gives group means 8 and
4 nm, three independent fictional preparations in each group and SEM
`2/sqrt(3)` nm. It does not fit a group difference, establish biological
validity or confirm the independence declaration. Software modules can live in
separate owning repositories; project-specific plans/configurations stay with
the research project. Document each actual software revision in Methods.

## What is preserved

Every execution has its own `runs/run_…/` directory:

| Item | Recorded evidence |
|---|---|
| `preflight.json` and immutable preflight journal | Purpose, estimand, plan, attributed decisions, original locators, selection, source IDs/revisions and file hashes, units/hierarchy, QC, sensitivity/limitations, replay criteria |
| `code/`, `software.tar`, `working-tree.patch` | Git archive of the exact selected commit; executed-file hashes, repository/origin, tree/HEAD, dirty status and patch identity; dirty changes are never silently executed |
| `inputs/` | Separate selected-file copies, checked against original hashes during snapshot |
| `config.json`, `request.json`, `bootstrap.py` | Actual configuration, resolved request and entry invocation |
| `environment.json` | Python implementation/version/executable hash, OS/architecture, installed dependency versions, runner/calculator hashes and committed environment/lock-file hashes |
| `active.json` | Owning host/process identity and current phase, supporting interruption diagnosis |
| `stdout.log`, `stderr.log`, `final.json` | Execution result, errors, exit code, timestamps, retained partial outputs, QC and output/log hashes |
| Workspace run/analysis records | Immutable preflight and outcome, input revision links and a current unreviewed analysis when appropriate |

The preflight journal is persisted **before launching Python**. Outcome records
are separate and immutable. Failed/interrupted/QC-failed outputs remain on disk.
Updates to source records invalidate dependent analyses through the existing
workspace provenance graph. A source file changed outside the record store is
reported by verification; historical snapshots remain available for replay.

Local remote-tracking refs report whether the commit is known to a cached
remote branch. This is labelled `cached_remote_contains`, never a live push
verification. The runner does not fetch or push. The host must verify the actual
GitHub revision before declaring a relied-upon module accessible or publishing
a release. A missing remote is explicitly unverified.

## Replay, interruption and re-entry

`verify_run` checks manifests, complete copied input/code inventories, outputs
and final logs against the immutable workspace journal. It separately reports
changes to current original files/records. Modified snapshots or outputs block
replay. This provides local tamper evidence; it is not adversarial attestation.

`replay_run` copies the preserved committed source and selected inputs into a
new run, uses the recorded configuration/seed, and compares all output names
and bytes. `numeric_json` permits numeric JSON leaves to differ within the
**predeclared** absolute/relative tolerances; text, units, booleans, keys and
array order still must match. Other file types require exact bytes. Use
deterministic plot metadata for byte-identical SVG/image replay or add a
scientifically meaningful canonical numeric output. Do not broaden a failed
tolerance after inspecting results without recording a new analysis decision.

Replay requires the recorded Python, package inventory and runner/calculator
hashes. It does not install dependencies or recreate an environment. Restore
the recorded pinned environment through its owning software procedure first.
Packages imported from outside the committed snapshot are identified by the
environment inventory; arbitrary editable/transitive module bytes are not
automatically vendored. Exact LLM wording is outside executable replay.

Timeout or host interruption terminates the launched process group where
supported and records `interrupted`, logs and partial artifacts. If the host
process exits abruptly, a prepared run remains. `recover_run(workspace,
run_id, note)` closes an abandoned journal after checking that its recorded
processes are no longer active. It never silently reexecutes work. Completed
runs are returned as already finished. Review failures, decide the narrowest
fix, commit it, and start a new recorded run; preserve the earlier failure.

## Scope and limitations

This is **explicitly trusted code execution, not a security sandbox**. The
pipeline runs with the OS user's rights and can perform arbitrary Python
actions; host authorization/code inspection remains essential. Shell strings
are not executed: Python and Git receive argument arrays. The environment
omits host credentials; credentials in specifications are rejected and
credential-shaped log/patch text is redacted. Code/data/artifacts themselves
may contain private information and must be inspected before external release.
The service neither requests network access nor enforces a network firewall.
It does not install packages, use paid APIs or invoke a remote model.

Regular files and physical repository/input paths are supported. Symlinks,
junction inputs, Git submodule contents and `.upstream` private source clones
are rejected. Code archives are limited to 256 MiB and 20,000 members; select
1–128 explicit input files. Inputs are streamed/copied without a dataset-size
cap, so the host must assess available storage before selecting large data.
Git archive respects committed export attributes; the exact archived files
are hashed. Missing selected entries fail rather than falling back to dirty
or unversioned files. Long jobs and pipelines that detach descendants require
host process supervision; this prototype does not promise a distributed job
scheduler or automatic resume inside an arbitrary Python algorithm.

The argument-array and environment behavior follows the
[Python subprocess documentation](https://docs.python.org/3/library/subprocess.html).
Committed source packaging uses
[Git archive](https://git-scm.com/docs/git-archive).
