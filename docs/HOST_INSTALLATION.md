# Install the conversational prototype

Requires Python 3.12 or newer and a capable agent host with local file and command
tools. Git is required for versioned execution. The exact environment is in uv.lock.
No model API key is required when using the authorized inference of your existing
host. Host usage/account limits still apply.

## Python tools

From the product checkout:

```text
uv sync --locked --extra mcp --group dev
uv run scientist-os host --workspace research catalog
```

Or install the inspected wheel in an isolated environment:

```text
python -m venv .host-env
.host-env/Scripts/python -m pip install scientist_os-0.3.0b1-py3-none-any.whl
```

Use `.host-env/bin/python` on Linux/macOS. Install the `mcp` extra when setting up
the optional server. The wheel contains all scientific skill references/templates;
the source distribution also contains examples, manuals and tests. Keep research
workspaces and original sources outside version-controlled software release paths.

## Host skill or plugin

The distribution contains `host-package/scientist-os`, a standard local plugin
with `.codex-plugin/plugin.json` and the `scientist-os` skill. Install it from a
configured local personal marketplace using Codex's plugin installation flow.
The current build session installed this package as `scientist-os@personal`.
Start a new conversation so the host discovers newly installed resources.

A simpler host adapter copies the same skill into the host's supported skill folder:

```text
scientist-os host install-skill --destination PATH_TO_HOST_SKILLS/scientist-os
```

Existing different files are not overwritten. This installs procedures, not host
credentials, tools, inference, a scheduler or another conversation UI. If the host
cannot find `scientist-os`, point it at the installed environment's Python and use
`python -m scientist_os.cli host ...`. Keep the full tool path in the project's
start instruction when needed. Do not transplant another user's absolute paths.

The verified local delivery uses `uv tool install` with the inspected wheel and
constraints exported from `uv.lock`, plus the MCP extra. `uv tool dir --bin` finds
the installed command directory; `uv tool dir` finds its isolated environment.
If that directory is absent from PATH, invoke the full executable path or use
the supported `uv tool update-shell` setup and restart the shell. A fresh host
conversation must be given the research-workspace location, not just a plugin name.

## Optional scientific MCP server

The CLI is the tested default in the capable local host. Hosts with MCP stdio
support can connect the same services with the exact command:

```text
python -m scientist_os.host_cli --workspace ABSOLUTE_RESEARCH_ROOT --permit-root ABSOLUTE_INPUT_ROOT mcp
```

Configure that command and argument array through the host's supported MCP settings.
The server exposes a catalog and scientific operations; it supplies no model loop.
`--permit-root` can be repeated for explicitly authorized additional input/code roots.
The workspace itself is permitted. Never bind broad roots merely to silence a
permission error. Scientific records returned over MCP can reach the host/model:
local stdio does not prove local inference or authorize private-source disclosure.

The older `scientist-os-mcp` command is the historical four-tool, selected-record
bridge. Use the command above for the new action-capable interface. Dynamic plugin
MCP installation and MCP Apps embedding are not needed for the tested CLI route.

## Start instruction

> Use Scientist OS. Open my selected research workspace, read its durable context
> and pending tasks, and help me continue through conversation. Use the configured
> Python tools and your available host capabilities. Ask only about material missing
> scientific facts or decisions; preserve source authority, originals and history.

For a complete fictional example, build the mixed folder using
`scripts/make_conversational_fixture.py`, then follow
`examples/conversational/journeys.md` through the host. Generation needs reportlab
in the artifact-building environment; it is not a scientific-core dependency.

## Backup and restore

Close writers and back up the complete research directory, including SQLite,
attachments, execution snapshots, exports, review baselines and context views.
Original external sources require their own backup. Restore into a new directory,
verify the record audit and representative run hashes, then reconcile path changes
before replay. The current prototype records absolute external locators; moving a
workspace requires that explicit reconciliation. It does not claim automatic
cross-machine restore certification or source/cloud synchronization.
