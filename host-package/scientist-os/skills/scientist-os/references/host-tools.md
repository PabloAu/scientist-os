# Host tools and portable execution

The skill is the scientific procedure, not a separate model or chat application. The initial adapter uses the installed `scientist-os` Python command through the capable local host. A focused browser view may inspect records/artifacts; conversation remains in the host.

## Discover the installed interface

Use the current catalog before constructing operation arguments:

```text
scientist-os --help
scientist-os host --workspace <permitted-project-root> catalog
scientist-os host --workspace <permitted-project-root> call <operation> --arguments <arguments.json>
```

For an already authorized source or software folder outside the project, add `--permit-root <authorized-folder>` before `catalog` or `call`; repeat it for additional explicit roots. A path mentioned inside argument JSON does not grant access. Scope additional roots narrowly to the scientist's request. The service allowlist is a connection boundary; the host's independent filesystem/code tools still follow their own permissions and the project authorization.

Write argument JSON as a file to avoid shell interpolation and quoting mistakes. Read a failed operation's message and correct the concrete cause. Do not guess an argument schema, silently fall back to the legacy answer-only runtime, or treat a success flag as scientific approval. If a catalog entry lacks nested fields, read the installed API guide or operation's Python contract. The equivalent MCP tool names replace operation dots with underscores when that server is configured; discover the actual server tools. An installed skill alone does not configure an MCP connection.

The catalog groups project context/memory, tasks and action checkpoints, scientific records/states, ingestion, record lookup/update, analysis/replay, meta-analysis, manuscript/presentation editing, artifact export/inspection, reviewer rounds and problem capture. Read a record with its metadata, links, revision, review state and authority. Follow implicated links in both upstream and downstream directions rather than manually asking the scientist to select all context.

Three integrated operations address common cross-stage handoffs. `ingest.reextract` retries a parser against the exact preserved original with a revision guard and affected-record report. `analysis.register_result` binds a selected supported numeric JSON output and figure title to an intact completed Python run before authoring. `review.request` records exact accepted `evidence_ids` revisions, which `review.check` checks for later changes. Read the relevant corpus, analysis or review reference before using them; none grants scientific approval.

If the command is unavailable, inspect the project's installation manual and environment. A supported environment can call the same Python services. Document a missing dependency or host capability; do not imply a command executed when only proposed. The legacy web agent with selected-text retrieval is a separate limited surface.

## Host capability check

Record observed host/model identity when exposed, procedure/tool version, allowed roots, Python runtime, Git access, browsing, original-document/vision tools, editable artifact creation/rendering, active steering/resume and delegation. Mark capabilities as observed in this task, software-tested, available but unexercised, unavailable, or untested. Do not infer one from another. Never probe credentials by printing secrets.

Use native host tools when appropriate: browse primary literature; inspect permitted folders and original document pages; write/version Python in its owning repository; execute bounded local jobs; render/open editable artifacts and act on selected passages/slides. Honor source disclosure scope and existing authorization. Checkpoint general host actions as well as service calls. Use the host's approved authentication flow; no token borrowing or new paid API/compute is implied.

## Checkpoint contract

Before execution, save action identity, purpose, exact inputs/configuration, planned outputs and status. After execution, record actual command/tool, version, status, observations, outputs and hashes. On interruption, inspect the action journal and filesystem before retrying. Reconcile outputs of uncertain completion; do not repeat a publication, message, submission or other external action based solely on a missing completion marker. An action journal supports recovery; it is not an automatic exactly-once guarantee.

Use `task.begin_action` before the actual action and `task.finish_action` after observing its result. After an interruption, `task.recover` identifies uncertain action state; `task.reconcile_action` records the observed outcome with evidence and actor. Reconciliation does not itself rerun the action. Reusing an action key never authorizes duplicate execution. Do not call recovery while the original host operation is still running.

`project.context` includes pagination and text-truncation markers. Follow `next_offset` for complete relevant coverage and use located record reads for truncated content. Generated `host-context/CONTEXT.md` and JSON are disposable views of the canonical SQLite records; edit through project/record operations, then regenerate views. Editing an exported view is not an imported scientific correction.

For a new host, carry project evidence, decisions, task checkpoint and files, then repeat the capability check. Proprietary transcript context and hidden model state are not portable scientific evidence. Keep prompts/tool observations needed for the scientific account with privacy handling; keep secrets out of run records.
