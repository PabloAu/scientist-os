# Extend the conversational prototype

The host owns conversation, inference, tool choice, permissions and artifact
interaction. Scientist OS owns scientific records and reproducible service
operations. Keep these boundaries visible when adding a host or model.

## Service boundaries

`HostTools(workspace, permitted_roots)` fixes the scientific connection's roots.
`catalog()` returns operation signatures; `call(operation, arguments)` journals a
preflight and a completion/failure. The CLI and optional FastMCP stdio adapter use
this same dispatch. Prefer meaningful scientific operations over exposing a shell
as an opaque application tool. Host general tools remain governed by the host.

| Module | Responsibility |
|---|---|
| `workspace.py` | Stable records, optimistic revisions, history, links, current lineage and immutable service run records |
| `host_state.py` | Project context, decisions, source authority, scientific states, durable tasks and action recovery |
| `ingestion.py` | Permitted-folder inventory, preserved bytes, extraction locators/gaps, original inspection and re-extraction |
| `execution.py` | Committed Python snapshots, explicit inputs/config/environment, subprocess/QC records, verification and replay |
| `meta_review.py` | Traceable selection/extraction, comparability, frozen protocols and synthesis/sensitivity artifacts |
| `governance.py` | Panel contracts, frozen review packages, evidence-bound requests and verified problem resolution |
| `host_tools.py` | Host action binding, exact passage edits, run-to-figure registration, exports and inspection receipts |
| `studio.py`, `publishing.py`, `service.py` | Reused scientific authoring, numerical figure rendering and editable exports |
| `host_cli.py` | CLI, skill installation and optional full scientific MCP adapter |

## Add a versioned Python pipeline

Keep implementation in a dedicated Git repository. Commit the exact code and
environment/lock files. The callable script or module accepts
`--scientist-os-request PATH`; that JSON provides copied input paths, configuration
and an output directory. Write outputs only to that declared directory and emit
`qc.json` with an explicit boolean `passed`. See the complete
[execution contract](EXECUTION.md) and the core-backed
[example pipeline](../examples/pipelines/summary_pipeline.py).

The scientist or authorized host specifies immutable revision, explicit input
selection, units, independence hierarchy, estimand, plan, exclusions, missingness,
uncertainty, limitations and attributed decisions. The runner does not install
dependencies, infer a correct environment or certify code safety. Check a small
representative run before long jobs; use one GPU job at a time when applicable.

Register a supported numerical JSON output with `analysis.register_result` to
produce a current authoring figure. It verifies the original run, selected file
hash and linked input freshness. Other output types need a reviewed adapter;
never assume an arbitrary JSON object is a valid scientific result. Results
remain unreviewed and retain exact run/source identities.

## Add a tool or artifact adapter

Implement a small service with typed/validated arguments and a narrow responsibility.
Bind it in `HostTools.operations`. Preserve input revisions and history, validate
paths at the boundary, and make action outcomes inspectable. Distinguish historical
snapshots from current dependencies. A decision's historical fingerprint must not
become a live link that invalidates itself during evidence-state bookkeeping.

Use meaningful regression tests for leakage, stale evidence, boundaries,
independence, failed/partial execution or output integrity. An exporter requires
actual rendered-output verification in addition to structural tests. A new source
parser must preserve originals and report missing figures/tables/OCR explicitly.

Update the owning skill reference, coverage row, manual and capability claim.
Record a real failure and representative recheck before promoting a workaround
into a procedure. Do not copy private source text into the public skill.

## Add another host

Install the generic skill using that host's supported discovery mechanism and
connect the CLI or MCP command. Check actual conversation/tool invocation, explicit
root handling, browsing, original visual inspection, editable artifact interaction,
permissions and fresh-context recovery. Re-run the
[nine journeys](../examples/conversational/journeys.md) with real authorized
inference and preserve the trace. Canned outputs and protocol initialization alone
do not establish host capability. Declare missing tools and reduced scope.

The older API `Provider` and bounded browser agent are retained for legacy views.
Adding a provider there does not make that agent action-capable. Do not infer
desktop subscriptions, connectors or hidden context from an API SDK connection.

## Release and review

Build from explicit public paths, run the release-member/link check, inspect the
actual wheel/source archive and install the wheel in a clean environment. Keep
workspaces, artifacts, originals, credentials and local runtime paths out of Git.
Record the exact tested software and dependency versions; distinguish automated
tests from live host journeys and from human scientific validation.
