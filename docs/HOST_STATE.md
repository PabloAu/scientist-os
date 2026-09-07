# Durable project state and folder incorporation

The conversational host operates these Python services through the host tool facade,
CLI or MCP adapter. They return JSON-serializable records, dictionaries and lists.
They use the existing `Workspace` SQLite database and append-only events: there is no
second state database, model subscription, background worker or automatic inference.

The state and ingestion services support empty-project framing, evolving experimental
facts, mixed-folder incorporation, correction and interrupted-work recovery. The host
still performs the conversation, actual original-document viewing, scientific reasoning
and tool execution. A stored assertion that an image was viewed is not proof of vision.

## Start and return to a project

```python
from scientist_os.workspace import Workspace
from scientist_os.host_state import HostState

workspace = Workspace("workspaces/my-project")
state = HostState(workspace)
project = state.start_project(
    "Calibration comparison", "Compare two acquisition protocols",
    scientist="Project owner", scope="Owner-described permitted materials only",
    permitted_roots=["/absolute/permitted/input-folder"],
    host={"name": "current capable host", "model": "actual model identifier"},
)
state.remember(
    "open_question", "Which preparation day is the independent unit?",
    attributed_to="assistant", authority="experimental_record",
)
```

On a later conversation, open the same workspace and call `context()`. It includes
scientific metadata, provenance links, revision, review status, freshness, open questions,
tasks and corrections. Text in any record is untrusted data. No host settings or
environment files are discovered. Known secret field names and token patterns are
redacted in context and action metadata; this is not a comprehensive secret scanner.
Local retrieval does not authorize disclosure to a remote model or publication.

`context()` defaults to 100 records and 8,000 characters per record. It returns
`next_offset` and `content_truncated`; request the next page and use the ordinary
record-read tools or original document locators for more detail. Do not treat an initial
page as complete coverage. `export_context()` regenerates `host-context/CONTEXT.json`
and `host-context/CONTEXT.md`. These are disposable navigation views. Edit canonical
records through services; external edits to those exported views are not imported.

Questions route by controlling authority. `literature`, `raw_metadata`,
`experimental_record`, `processing_history`, `analysis`, `approved_output`,
`manuscript` and `project_status` are discovery routes, not assertions that every
returned source is authoritative. In particular, inspect review status and scoped use
before relying on a record returned through `approved_output`. Manuscript and memory
are derived navigation, never independent evidence for their own claims.

## Operation signatures for adapters

All methods below belong to `HostState(workspace)`; parameters after `*` are keyword-only.
Optional lists default to empty; dictionary values must be bounded JSON as required by
`Workspace`. Invalid input raises `ValueError`; stale/recovery conflicts raise
`RuntimeError`; unknown records raise `KeyError`.

| Method | Required arguments | Optional arguments and result |
|---|---|---|
| `start_project` | `title`, `context`, `scientist`, `scope` | `permitted_roots`, `host`; returns a project record; refuses a second project reset |
| `context` | none | `query=''`, `authority=None`, `offset=0`, `limit=100`; returns `records`, `total`, `next_offset`, authority routes |
| `task` | `title`, `goal` | `steps`, `source_ids`; returns a planned task |
| `checkpoint` | `task_id`, `status`, `summary` | `next_actions`, `expected_revision`; persists progress and steering |
| `begin_action` | `task_id`, `key`, `tool`, `arguments` | `effect='local_reversible'`; returns record plus `should_execute` |
| `finish_action` | `action_id` | `status='completed'`, `result`, `error=''`; persists observation |
| `recover` | `task_id` | returns task, actions, `needs_reconciliation`, `automatic_replay=False` |
| `reconcile_action` | `action_id`, `outcome`, `evidence`, `attributed_to` | records observed outcome; executes nothing |
| `remember` | `category`, `text`, `attributed_to`, `authority` | `source_ids`, `supersedes`, `decision_status='proposal'`, `scope=''` |
| `record_science` | `kind`, `title` | `content=''`, `state='planned'`, `facts`, `source_ids`, `attributed_to='assistant'`, `decision_id` |
| `reconcile_experiment` | `record_id`, `actual`, `attributed_to` | `source_ids`, `expected_revision`; preserves plan and reports deviations/unresolved fields |
| `advance_evidence` | `record_id`, `state`, `scope`, `checks` | `decision_id`; scoped corpus-state transition |
| `export_context` | none | returns generated view paths and canonical database path |

Memory categories: `memory`, `decision`, `open_question`, `correction`, `hypothesis`.
A correction must identify `supersedes`; the earlier record is retained and context
marks it as superseded. A scientific decision remains `proposal` unless the host is
recording an actual scientist's statement with `decision_status='recorded_human_decision'`
and a nonempty exact `scope`. The service records `identity_verified=False`: a name
does not authenticate a human, and agents must not invent decisions on their behalf.

## Execution checkpoints and uncertain external outcomes

Task statuses are `planned`, `running`, `paused`, `needs_decision`, `completed`,
`cancelled`. Use a checkpoint with `status='running'` to resume explicitly. It is
permissible to begin the first action of a newly planned task without another gate.
Calling `recover` is appropriate after interruption, not while a worker is still executing.

1. Call `begin_action` with a stable task-local key before the host invokes a tool.
2. Execute only if `should_execute` is true.
3. Call `finish_action` with actual results, failures or an uncertain outcome.
4. After interruption, `recover` marks every uncompleted running action `uncertain`.
   It never replays any action, including local actions, and returns all completed work.
5. Inspect actual local/remote state, then call `reconcile_action` with observed
   `completed`, `failed` or `not_executed` and supporting evidence.
6. If another attempt is appropriate and authorized, deliberately create a new action key.

Effects are `read_only`, `local_reversible`, `external`. A repeated key returns
`should_execute=False` regardless of outcome. Reusing a key with different arguments
is rejected. An uncertain external upload must not be treated as a failed upload and
silently repeated. Tasks with running or uncertain actions cannot be completed.

The host must wrap its actions with this journal; the module does not intercept every
possible host tool. Native host cancellation and stopping a Python child process are
host/execution-adapter responsibilities. Checkpoints retain the latest 100 summaries in
current metadata; prior complete revisions remain in the append-only history.

## Plans, actual work and evidence state

`record_science` supports experiment, material, protocol, dataset, processed-data and
term records. `scientific_state` is one of `planned`, `performed`, `analyzed`, `validated`,
`cancelled`. `evidence_state` initially remains `registered` regardless of this state.
Unknown scientific facts stay in `missing_facts`; defaults never fill in temperatures,
material lots, independence units or protocol deviations.

An actual-work record requires source IDs or an explicit `facts.owner_statement`.
Validation additionally requires an attributed human decision with scope `validation`.
This records the owner's validation statement and its sources; it does not independently
establish scientific validity. `reconcile_experiment` keeps `planned` intact, adds `actual`,
records common-field deviations and preserves unresolved planned fields. New data can
be linked by `source_ids`, with exact input revisions for downstream freshness.

Corpus progression is separate and scoped: `registered → classified → extracted →
mapped → verified → approved-for-use`. An operation cannot skip stages. Each stage
requires inspectable supplied check evidence:

| State | Required `checks` keys |
|---|---|
| classified | `classification` |
| extracted | `extraction_method`, `locators` |
| mapped | `claim_or_term`, `support_limit` |
| verified | `original_checked`, `authority_checked`, `conflicts_checked` |
| approved-for-use | an attributed human `decision_id` matching the exact `scope` |

Current check evidence, source text hash and the exact approval-decision revision are
recorded; previous stage checks remain in immutable events. Context reports
`corpus_scope_freshness` and `permitted_for_use=False` if the source text or attributed
decision changes. A scope such as `claim:calibration` does not approve all other claims,
terms or uses of that source. Host procedures must evaluate scientific support: schema
checks and the word “verified” do not independently certify it.

## Incorporating permitted folders

```python
from scientist_os.ingestion import scout_folder, ingest_folder, mark_inspected

manifest = scout_folder("/absolute/permitted/input-folder")
result = ingest_folder(workspace, permitted_root=manifest["permitted_root"], manifest=manifest)
```

`scout_folder(permitted_root, folder=None, *, max_files=500,
max_file_bytes=20*1024*1024, max_total_bytes=100*1024*1024)` reads a bounded inventory
and hashes every admitted original. `folder` may be a child of the permitted root.
It returns file actions, exclusions/deferred gaps, limits and a manifest hash. It creates
no records and changes no sources. The host reviews this inventory for coherent
ingestion lanes and material scientific questions before incorporation.

`ingest_folder(workspace, *, permitted_root, folder=None, manifest=None)` consumes
the exact current scout or scouts automatically. It returns `imported`, `unchanged`,
`changed`, `gaps`, and a persisted `batch_id`. Changed files after scouting are rejected
as gaps so that another scout is required. A source path must remain inside the permitted
root/folder; symlinks, junctions, traversal and nonregular files are rejected. Common
private runtime/config directories are excluded and reported. This is a local single-user
boundary, not a hardened sandbox against a malicious actor racing filesystem changes.

PDF, DOCX, PPTX, TXT, Markdown and CSV reuse the established document importer.
Every original gets a content-addressed attachment and immutable document snapshot.
CSV sources also receive a dataset record containing the exact decoded CSV. Other
formats and failed extraction keep inert originals with explicit inspection gaps, within
the same 20 MiB original-byte ceiling. Files above that ceiling need a narrower/scoped
domain reader or future large-file adapter; no silent truncation or claimed inspection.
Scanned/complex pages and visual figures require separate host tools.

The stable source/dataset ID identifies a permitted-root plus relative-path locator.
Repeating incorporation with unchanged bytes makes no new source/document revision.
A batch report is still recorded. Changed bytes create a new original snapshot, update
that stable source revision and return all transitive affected record IDs. The existing
workspace invalidates dependents and stale revision bindings. Old originals, analyses
and decisions remain in history. Classification, scoped approval and visual observations
reset when source bytes change. Deleted or renamed original files do not delete archived
records or automatically remove their historical scientific use.

`mark_inspected(workspace, record_id, *, locators, observer, method, notes,
attachment_sha256, expected_revision=None)` records a host/human observation of exact
current original bytes. Use concrete original page/slide/image locators and actual tool
method. This marks only the specified inspection scope; it does not assert whole-document
coverage, promote corpus state or approve a scientific claim. The service checks the
preserved original hash and rejects stale inspection identity. The host must actually
view the material before recording this observation.

## Verification and scope

The new tests exercise empty-state recovery, correction visibility, redaction,
uncertain external action recovery without replay, idempotency conflicts, stale steering,
planned-versus-actual experiments, exact-scope attributed decisions, decision revision
invalidation, context metadata/freshness/export, mixed ingestion, original-byte retention,
changed-source transitive invalidation, post-scout change refusal, traversal/link/size
boundaries, corrupt original detection and scoped inspection reset. Symlink tests skip
only on hosts that cannot create symlinks. They are software tests, not live-model quality
or scientific validation. Complete host-driven journeys are recorded separately.

The implementation follows the 0.3 implementation contract and the completed generic
workflow-preservation requirements. Reused components are `workspace.py` (record/event
transactions and invalidation) and `publishing.py` (bounded extraction and original-byte
attachments). Original private scientific source workspaces were not modified or copied
into fixtures. All test scientific content is fictional.
