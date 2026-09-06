# Contributing

Strengthen a real scientific workflow while preserving human control and traceable evidence.

```sh
uv sync --frozen --all-extras
uv run pytest
uv run ruff check src tests
uv run scientist-os demo --workspace workspaces/development
uv run scientist-os serve --workspace workspaces/development
```

Use a new demo directory if the existing one contains records. Stage explicit paths. Never add real lab data, unpublished manuscripts, credentials or proprietary records to fixtures.

## Interfaces

`workspace.py` owns records, references, reviews, transactions and history. `science.py` owns deterministic calculations and figures. `agent.py` owns selected-source access and proposals. `providers.py` owns transport. `mcp_server.py` exposes tools to external clients. `service.py` shares application actions; `app.py` and `static/` provide the local UI.

Use `Workspace.transaction()` for multi-record mutations and their events. A caught nested error still aborts the transaction. Freeze scientific input revisions, render/validate before saving, and reject stale lineage. Do not add alternate approval paths for model output.

## Model adapters

Implement the public `Provider` protocol. Test malformed responses, tool calls, timeouts, disclosure revocation, redirection and credential echoes. Report live-model compatibility separately with exact model/server versions; mocked transport is not a model-quality benchmark. See [PROVIDERS.md](docs/PROVIDERS.md).

## Scientific methods

Specify the estimand, independent unit, input schema, exclusions, uncertainty and failure conditions first. Include known-answer or trusted differential tests and misleading-replication cases. Preserve method/version/parameters and test output lineage. Register data/code/article links instead of copying a scientific application's implementation.

## Schema evolution

Database schema version 1 rejects unsupported versions. Changes require an explicit version bump, transactional migration, tested backup/recovery, fixture migrations and a changelog. Never silently reinterpret scientific meanings or rewrite historical events.

## Review and release

Keep PRs focused: explain user-visible behavior, assumptions, checks and limitations. Verify distributed archive contents and clean installation. Preserve failures. Do not claim performance, independent validation, contributor approval or release rights without evidence.

The demonstration and evaluation corpus are engineer-authored fiction. Independent model evaluations need a fresh frozen set and named human rubric review. Do not tune on published cases and call them held out.
