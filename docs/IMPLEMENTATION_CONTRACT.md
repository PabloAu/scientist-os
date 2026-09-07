# Implementation contract

## 0.3 conversational prototype (supersedes conflicting historical restrictions)

The primary runtime is a capable local agent host with installed scientific skills,
Python CLI tools, durable scientific state and native artifact previews. Host tools
may inspect permitted files, browse, edit and execute Python, delegate disjoint work,
and create/revise derived artifacts under existing task authorization. The legacy
selected-record proposal runtime remains a supported narrow beta surface, not the
Scientist OS conversational runtime. Its prohibition on arbitrary execution and its
selected-record context restrictions apply only to that legacy runtime.

Scientific approval is a distinct attributed human decision. Agent-generated drafts,
plans, extracts and calculations do not become approved through execution. Sources
remain private/immutable; portable workflows and fictional fixtures are releasable.
No additional paid inference or compute is authorized. Use the current host's actual
inference and tools and report capability-specific demonstrations honestly.

Current disjoint ownership: state agent owns new `host_state.py`, `ingestion.py`
and their tests; analysis agent owns new `execution.py`, `meta_review.py`, their
tests and analysis fixtures; procedure agent owns `host-package/` and workflow
coverage/procedure documentation; lead owns integration, CLI/MCP, installation,
artifacts, verification and other files. Do not change another lane without agreement.

## Historical 0.1/0.2 contract

Version 0.2 extends this base contract with [authoring studio](STUDIO_CONTRACT.md),
[publishing/library](PUBLISHING_CONTRACT.md), and [release scope](AUTHORING_RELEASE.md).
The historical ownership list below describes the first beta. During 0.2, studio
owns studio.py/new kinds, publishing owns publishing.py, the frontend agent owns
static/, and the lead owns HTTP integration, literature, examples and release.

Python >=3.12, uv, src layout. Local FastAPI application with a packaged static browser UI. SQLite persistence. Installable CLI. No hosted service is promised for the private-data beta. A model-free synthetic example must work immediately. JSON and Markdown exports preserve provenance and review state.

## Ownership

- Core agent: `src/scientist_os/workspace.py`, `tests/test_workspace.py`.
- Runtime agent: `src/scientist_os/agent.py`, `src/scientist_os/providers.py`, `src/scientist_os/mcp_server.py`, `tests/test_agent.py`, `tests/test_providers.py`, `tests/test_mcp.py`, `docs/PROVIDERS.md`.
- Scientific methods agent: `src/scientist_os/science.py`, `tests/test_science.py`, `docs/METHODS.md`, `docs/SOURCE_AUDIT.md`.
- Lead: everything else and final integration. Do not edit another owner's files without coordination.

## Workspace API (core implements; other components consume)

All return JSON-serializable dicts/lists. `Workspace(root: str | Path)` initializes/opens a local directory and SQLite database. Exceptions are `ValueError` for rejected input, `KeyError` for missing record, `RuntimeError` for stale revisions/integrity conflicts. Methods are safe across separate request connections. SQLite transactions must couple changes and audit events.

- `create_record(kind, title, content='', metadata=None, links=None) -> dict`
- `get_record(record_id) -> dict`
- `validate_current(record_id) -> dict` (checks all declared ancestor references without returning ancestor content)
- `transaction()` (atomic multi-operation context; nested errors mark it rollback-only)
- `list_records(kind=None) -> list[dict]`
- `update_record(record_id, *, expected_revision, title=None, content=None, metadata=None, links=None) -> dict` (resets review state)
- `review_record(record_id, *, expected_revision, decision, reviewer, note='') -> dict`, decision `approved` or `rejected`; approval does not prove scientific truth.
- `search(query, record_ids=None, limit=10) -> list[dict]` (exact excerpts/lexical search only, bounded)
- `audit() -> list[dict]` (finding fields `severity`, `code`, `record_id`, `message`)
- `events() -> list[dict]`
- `save_run(run: dict) -> dict` (assign id if absent, persist run plus event; never raw credentials)
- `list_runs() -> list[dict]`
- `get_run(run_id) -> dict`
- `export_bundle() -> dict` (records, events, runs, schema version, integrity manifest; no external file traversal)

Record keys: `id`, `kind`, `title`, `content`, `metadata`, `links`, `revision`, `sha256` (UTF-8 content hash), `review_status` (`unreviewed`, `approved`, `rejected`), `created_at`, `updated_at`. Immutable generated identifiers with kind prefixes. Allowed kinds: `source`, `dataset`, `material`, `protocol`, `processed_data`, `analysis`, `output`, `claim`, `term`, `experiment`, `manuscript`, `software`, `decision`, `note`. Metadata is bounded JSON; scientific fields, e.g. authority, license, external_allowed, units, independence_unit, protocol_version, code_commit, remain explicit rather than inferred. Links must reference existing records; no self or dangling references. No deletion in beta. Source citations use `{record_id, quote, sha256}`. Content changes invalidate related citation integrity; review state must not remain implicitly valid.

## Agent API (runtime implements)

`AgentRunner(workspace, provider).run(question, source_ids, *, task='answer', style='', max_steps=8) -> dict`.

Provider adapter has `name`, `is_remote` and `complete(messages, tools) -> dict` returning an OpenAI-style assistant message (`content`, optional `tool_calls`). `DemoProvider` exercises the real bounded tool loop deterministically and labels itself as a demo, never an LLM. `OpenAICompatibleProvider(base_url, model, api_key=None, timeout=30, max_tokens=2048)` supports explicit local loopback HTTP or HTTPS remote endpoints, no redirect following, bounded requests. `ScriptedProvider` may exist for tests. Follow-up corrections are new runs; no hidden conversation or automatic private-context inclusion.

Allowed agent tools: `search_records(query)` across selected IDs only; `read_record(record_id)` selected IDs only; `finish(answer, citations)` where citations are exact source quotes and hashes. Use selected IDs, freshness and disclosure policy checks before every external call. Remote providers require metadata `external_allowed: true` on EVERY selected record. Tool results never include arbitrary workspace config, all-records export, filesystem or secrets. A completed answer is `needs_review`; an answer with no valid citations is clearly unsupported/abstained. No auto-approval or external action. Tasks: answer, audit, experiment, meta_analysis, manuscript, terminology, journals, figures. They are agent proposals; deterministic analyses have separate explicit UI actions. Bound iterations, selected content, question/style lengths, response sizes and record count. Trace every tool call and error; record configured limits and provider/model identity. Do not claim token cost when unavailable.

## Scientific API (methods agent implements)

Independent pure functions, no Workspace coupling or network:

- `summarize_csv(text: str, *, value_column: str, group_column: str | None = None, unit_column: str | None = None) -> dict`; parse numeric values strictly, report missingness/exclusions, group estimates at declared independent unit, reject nonfinite values and duplicate unit assumptions; no automatic causal inference.
- `meta_analysis(studies: list[dict], *, model='random') -> dict`; each row has study_id, effect, standard_error, optional independence_id; inverse-variance fixed and DerSimonian-Laird random effects, normal CI with limits, Q/I2/tau2, explicit small-k caveat, unique independent studies, no automatic meta-analysis from extracted prose.
- `render_figure(result: dict, *, title: str = '') -> str`; safe SVG string generated from deterministic results (forest for meta, group summaries for CSV), escape labels, include method/units limitations.
- `audit_records(records: list[dict]) -> list[dict]`; scientific completeness/bias flags on provenance, independence, protocol versions, software immutable revisions, unsupported/causal claims; rules labelled screening, not proof of bias.

The lead integrates these into revision-bound analysis records and output lineage. No arbitrary code execution, silent exclusions or file access.
