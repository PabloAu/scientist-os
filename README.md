# Scientist OS

**Your evidence, methods, analyses and article—with a traceable assistant and a human in charge.**

Scientist OS is a local research workspace for individual experimental scientists. Write a manuscript section by section, build a presentation from current figures, discuss research directions, and keep each output connected to its sources, methods and data. You choose what the assistant can read and which proposed changes to apply.

**Version 0.2.0b1: an experimental authoring beta.** The calculation, persistence, tool-boundary and application workflows are tested on fictional fixtures. This is not validated scientific reasoning, an autonomous scientist, or a multi-user hosted service. The default assistant is a deterministic demonstration; real inference requires your model connection. See [verification and limitations](docs/RELEASE_CHECKLIST.md) and [model compatibility](docs/MODEL_COMPATIBILITY.md).

## Start in five minutes

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git, then:

```sh
git clone https://github.com/PabloAu/scientist-os.git
cd scientist-os
uv sync --frozen --all-extras
uv run scientist-os demo --authoring --workspace workspaces/teaching
uv run scientist-os serve --workspace workspaces/teaching
```

Open **http://127.0.0.1:8765** in your browser. No model account or API key is needed for the teaching example. Use Python 3.12 or newer; uv can provision a compatible interpreter. Stop the application with Ctrl+C.

For your own research, use a separate workspace:

```sh
uv run scientist-os init --workspace workspaces/my-research
uv run scientist-os serve --workspace workspaces/my-research
```

The interface and scientific data stay on your computer. External model transmission occurs only when you choose a configured external model and explicitly permit sharing each selected record and writing/discussion context. Explicit Crossref searches send only the public query you type. A local model server is responsible for its own onward network behavior; a local endpoint does not certify zero egress.

## Write and present your study

The writing example opens with a six-section manuscript, a registered figure, four editable slides, a reference, project notes and a discussion topic. All content is fictional.

1. Open **Manuscripts** and the teaching manuscript. Edit individual sections; attach figures and references; mark supplementary sections.
2. Select a passage, choose evidence and ask for a rewrite or provenance check. Inspect the suggestion and citations before applying it with your name. The default demo exercises the tools; connect a real model for actual language generation.
3. Inspect the assembled manuscript and download Word or HTML. References and supplements travel with it.
4. Open **Presentations**. Edit slide titles, body text, speaker notes and figure links, then download an editable PowerPoint deck.
5. Use **Project library** to import permitted PDFs, Word files, PowerPoint files, proposals or text. Register selected excerpts from long documents for bounded model use.
6. Use **References** to enter details or explicitly search Crossref. In **Discussions**, select project evidence and literature excerpts and discuss alternatives, controls or next experiments.

See the [authoring guide](docs/AUTHORING_GUIDE.md) for selection, review, reference, export and recovery details.

## Try one complete workflow

1. Inspect the two synthetic source notes, including the contradictory pilot, in **Research records**.
2. Open **Model runner**, select those notes, and ask what the example supports. The demonstration runs real search/read/finish tools without an LLM.
3. Inspect quoted passages and the tool trace. Save an **unreviewed draft**, then edit or review it.
4. Open **Analysis & figures**, choose *Synthetic fluorescence readings*, and use `signal`, `group`, and `day` as the columns.
5. Group means should be **11 and 14**, with **three independent days per group**. Twelve readings are not 12 independent replicates. This is a synthetic known-answer fixture, not a biological result.
6. Inspect parameters, input revisions and SVG. Review upstream records first. After reviewing an analysis, use **Regenerate linked figure** to bind a new figure to that revision.
7. Download JSON and Markdown from **History & exports**. Stop the application and copy the whole workspace directory, including attachments, for a restorable backup.

The [user manual](docs/USER_MANUAL.md) explains every screen, record type, review state and recovery path.

## What the beta does

| Research need | Implemented behavior |
| --- | --- |
| Data provenance | Stable IDs, content hashes, version history, input revisions and directed links among evidence, methods, data, analyses, outputs and claims |
| Materials and protocols | Versioned records with source locations, explicit uncertainty and dataset links |
| Evidence and bias audit | Citation/lineage integrity checks plus clearly labelled completeness and scientific-risk screening |
| Data analysis | Strict CSV input, missingness accounting and equal-weight independent-unit group summaries |
| Meta-analysis | Independent-study inverse-variance fixed-effect and DerSimonian–Laird random-effects calculations with heterogeneity and uncertainty |
| Figures | Reproducible SVG summaries and forest plots linked to calculation and input revision |
| Experiments and planning | Selected-evidence proposals; editable experiment and decision records |
| Article writing | Section editor and assembled manuscript, passage proposals with human apply, linked figures, bibliography, supplements, editable Word and HTML exports |
| Project documents | Original-byte PDF/DOCX/PPTX/text import, hashes, extracted page/slide/paragraph locators and selected excerpts; no OCR or layout reconstruction |
| References | Editable bibliography, explicit Crossref metadata search, links to separately imported full text |
| Presentations | Slide editor, four restrained layouts, registered figures, speaker notes and editable PPTX export |
| Research directions | Persistent evidence-scoped discussions, explicit prior-turn context, alternatives and proposed experiments; no implicit current-field knowledge |
| Journal selection | Evidence-backed proposal tasks; current journal facts require registered official sources |
| Terminology | Preferred terms, definitions, aliases, evidence links and revision review |
| Software/data/article association | Software records for repository URL, immutable commit, environment and run details, linked to analyses and manuscripts |
| Human control | Explicit source selection, editable drafts, named revision-bound reviews, stale-evidence invalidation and no model approval tool |
| Sharing and extensibility | Installable Python package, local browser UI, CLI, MCP tools and a small provider interface |

The beta does not automatically acquire restricted full text, perform OCR or table reconstruction, run arbitrary analysis code, operate laboratory equipment, submit articles or push to GitHub. An external agent may use its own tools for those tasks under its own permissions; Scientist OS does not sandbox that host. Keep large raw data in authoritative storage and register checked excerpts, metadata and immutable software references. Imported documents are reading aids, not independently verified evidence.

## Bring your own model

- **Compatible API:** configure a local or HTTPS OpenAI-compatible chat-completions endpoint and model name. Tool calling is required; compatibility varies by server and model.
- **Codex, Claude Code and other MCP clients:** the host supplies its own model. Scientist OS supplies selected-record read/search tools, task packets and validated proposal submission. There is no approval tool.
- **Custom adapter:** implement `Provider.complete(messages, tools)` for another API protocol. The scientific records and review logic remain unchanged.

See [provider configuration and MCP examples](docs/PROVIDERS.md). No model weights are bundled. A coding-assistant subscription is not assumed to include a separate API budget. No paid inference was used to verify this release.

## Why a local browser app?

It combines an approachable interface, local scientific data, cross-platform Python installation and an auditable repository. Shared hosting would require accounts, tenant isolation, quotas and data governance. A signed executable could simplify distribution later; neither is claimed in this beta. The Python and MCP interfaces support future interfaces without replacing the evidence model. See the [architecture](docs/ARCHITECTURE.md).

## Documentation

- [User manual](docs/USER_MANUAL.md)
- [Manuscript, library and presentation guide](docs/AUTHORING_GUIDE.md)
- [Model/API/MCP connections](docs/PROVIDERS.md) and [compatibility scope](docs/MODEL_COMPATIBILITY.md)
- [Scientific methods and assumptions](docs/METHODS.md)
- [Architecture](docs/ARCHITECTURE.md) and [development guide](CONTRIBUTING.md)
- [Source audit and migration](docs/SOURCE_AUDIT.md)
- [Evaluation protocol](docs/EVALUATION_PROTOCOL.md) and [synthetic cases](examples/evaluation_cases.json)
- [Release verification](docs/RELEASE_CHECKLIST.md), [security boundaries](SECURITY.md), and [changes](CHANGELOG.md)
- [Product roadmap and evidence gates](docs/PRODUCT_ROADMAP.md)

## Reproduce the checks

```sh
uv sync --frozen --all-extras
uv run pytest
uv run ruff check src tests
node scripts/check_frontend.cjs
uv build
uv run scientist-os audit --workspace workspaces/teaching
```

The MCP test launches a real stdio client and server. On Windows it needs ordinary process/pipe permissions; restricted agent sandboxes can block named-pipe creation before server startup. Run the release check on the normal host. Dependency deprecation warnings are documented in the verification record.

## Provenance and license

The reusable workflow was derived from private Cell-iSCAT-Writing revision `00273003a5154672583888c6993751ad463f977e`. Its clone is preserved locally in an ignored `.upstream` directory. This repository uses fresh product history and newly implemented generic code. No original manuscript, unpublished dataset, scientific screenshot, source record or private sibling application is included.

Generic software and workflows use [Apache-2.0](LICENSE). Original fictional fixtures use CC0-1.0 as described in [NOTICE](NOTICE). Third-party dependencies retain their licenses; no imported third-party skill code is redistributed. Pablo defines the scientific intent and release decisions. Agent-assisted engineering checks are separate from human scientific validation.
