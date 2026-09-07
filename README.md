# Scientist OS

**A scientific project companion inside your capable conversational agent host.**

Bring a permitted folder, ask a question, request an analysis, select a passage or correct an assumption. The assistant uses its available tools to do the work; Scientist OS preserves sources, scientific decisions, evidence states, versioned calculations, editable artifacts and a continuation point for the next conversation.

**0.3.0b1 is the first host-first conversational prototype.** It includes a portable scientific skill/plugin and a Python action interface. The local Codex host was exercised with actual authorized inference and tool execution across nine fictional journeys. This establishes a working software path, not human usability, scientific validity or equivalent capability on another host/model. Read the [verification record](docs/PROTOTYPE_VERIFICATION.md).

## Start through conversation

Install the Python package and Scientist OS skill/plugin using the [installation guide](docs/HOST_INSTALLATION.md). Open a capable host conversation with the skill available and say:

> Use Scientist OS for this research project. Read its saved context and pending work, or initialize it if empty. Incorporate the folder I have permitted, explain what it supports and what is missing, and continue through conversation. Preserve originals and ask me about material scientific facts or decisions.

The host needs the installed Python command, a selected workspace and explicitly permitted input/software roots. Its existing account supplies inference; no separate model API or paid compute is required by this package. Account limits and host data-handling policies still apply.

For a development checkout:

```sh
git clone --branch codex/conversational-prototype https://github.com/PabloAu/scientist-os.git
cd scientist-os
uv sync --frozen --all-extras
uv run scientist-os host --workspace workspaces/my-research catalog
```

See the [conversational manual](docs/CONVERSATIONAL_MANUAL.md) and [nine example journeys](examples/conversational/journeys.md). Conversations drive the tools; there is no prescribed sequence of record-selection forms.

## What accompanies the scientist

| Work | Prototype behavior |
|---|---|
| Mixed research material | Scout permitted folders; preserve original bytes; index experiments, protocols, materials, CSV, notes, PDF, DOCX and PPTX; retain unsupported/extraction gaps |
| Scientific reasoning | Source authority, competing explanations, controls, scoped decisions, inventory readiness, missingness and independent-unit accounting |
| Analysis | Execute explicitly trusted Python from an immutable Git revision on copied inputs; retain environment, configuration, decisions, logs, QC and output hashes; verify/replay |
| Controlled synthesis | Freeze scope, selection, exact extraction and comparability; calculate fixed/random effects and prespecified sensitivity analyses; expose unresolved judgements |
| Literature and visuals | Use the host's browsing/document/vision tools; record what was actually inspected and where gaps remain |
| Editable artifacts | Create and conversationally revise manuscripts, proposals, supplements, figures and presentations; export DOCX/PPTX/HTML/SVG/PNG and attribute exact-byte inspection |
| New evidence | Retain versions; identify affected analyses, figures, prose and decks; reject stale current exports; recompute and revise with history |
| Review and recovery | Freeze review baselines, track atomic requests and exact evidence, preserve human decisions, checkpoint tasks and reconcile uncertain actions before retry |

All ten original workflow stages and 53 detailed controls are mapped in the [coverage matrix](docs/WORKFLOW_COVERAGE.md). It distinguishes enforced code, host procedures, manual scientific judgement and demonstrated paths. A procedure's presence does not imply every branch has been empirically validated.

## Host and scientific boundaries

The current host supplies conversation, inference, browsing, file access, Python, vision and native artifact views. The core is provider-independent. The optional action-capable MCP server exposes the same scientific services; MCP does not supply an agent runtime or transfer credentials. See the [capability matrix](docs/HOST_CAPABILITIES.md).

This is a single-user local prototype. Trusted Python execution is **not a sandbox**. Local storage does not mean local model inference. Access is not publication permission. The package does not operate laboratory equipment, silently install analysis dependencies, procure compute, certify data rights or approve science. Scientific decisions remain attributed human judgements. Calculations and output identities are reproducible within declared environments/tolerances; identical LLM wording is not promised.

The v0.2 browser application remains available as a focused record and artifact editor. Its bounded Q&A provider and older four-tool MCP bridge are legacy interfaces. See the [legacy authoring guide](docs/AUTHORING_GUIDE.md) if that view is useful.

## Manuals and engineering

- [Installation](docs/HOST_INSTALLATION.md), [conversation](docs/CONVERSATIONAL_MANUAL.md), [state and recovery](docs/HOST_STATE.md)
- [Execution](docs/EXECUTION.md), [controlled meta-analysis](docs/META_REVIEW.md), [scientific methods](docs/METHODS.md)
- [Procedures](docs/SCIENTIFIC_PROCEDURES.md), [coverage](docs/WORKFLOW_COVERAGE.md), [capabilities](docs/HOST_CAPABILITIES.md)
- [Verification](docs/PROTOTYPE_VERIFICATION.md), [first host observations](docs/HOST_JOURNEY_OBSERVATIONS.md), [fresh continuation](docs/FRESH_RESUME_OBSERVATIONS.md)
- [Extension guide](docs/HOST_EXTENSION_GUIDE.md), [contributing](CONTRIBUTING.md), [security](SECURITY.md), [changes](CHANGELOG.md)

```sh
uv sync --frozen --all-extras
uv run pytest
uv run ruff check src tests scripts
node scripts/check_frontend.cjs
uv build
uv run python scripts/check_release.py
```

Real MCP subprocess tests need normal process/pipe permissions; restricted Windows agent sandboxes may deny named-pipe startup. Local live-host checks and automated cross-platform tests are reported separately.

## Provenance and license

The generic workflow derives from the privately preserved Cell-iSCAT-Writing workflow. Original scientific records, manuscripts, unpublished data and screenshots remain outside this repository and its distributions. Generic implementation and procedures use [Apache-2.0](LICENSE); original fictional examples use CC0-1.0 under [NOTICE](NOTICE). Dependencies retain their licenses. Pablo defines the scientific intent and decisions; agent-generated implementation and its checks are recorded separately from human scientific validation.
