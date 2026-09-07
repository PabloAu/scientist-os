> Historical v0.2 browser/bounded-provider documentation. For the current conversational prototype, start with [the host manual](CONVERSATIONAL_MANUAL.md) and [0.3 verification](PROTOTYPE_VERIFICATION.md).

# Model compatibility and validation status

This beta implements a provider-neutral research harness. It does **not** claim that every model or assistant application has been tested. Model quality, tool-call reliability, endpoint interoperability, and the scientific usefulness of responses require separate evaluation.

## What has been exercised

| Connection | Implemented | Evidence in this repository | Live-model validation |
| --- | --- | --- | --- |
| Deterministic demonstration | Yes; search → read → finish through the real runtime | Runtime tests and HTTP run → draft → reopen tests | Not applicable: the demonstration is not an LLM |
| Local compatible Chat Completions endpoint | Yes; explicit loopback HTTP/HTTPS | Mock HTTP request/response tests, runtime tests, and configured-provider HTTP integration tests | Not performed |
| Remote compatible Chat Completions endpoint | Yes; HTTPS and per-record disclosure permission | Mock HTTP transport, refusal before dispatch, selected-only context, redacted errors and credential echoes | Not performed; no paid API calls |
| MCP stdio harness | Yes; packet, selected read/search, proposal submission | Real SDK client/server initialize → list → read → submit round trip, including refused private read and unavailable approval tool | Protocol tested; no model-connected host session evaluated |
| Codex, Claude Code, or another MCP-capable assistant | The stdio server can be registered with a compatible host | A host-neutral executable/arguments configuration is in [PROVIDERS.md](PROVIDERS.md) | No host-specific model session certified by this release |
| Another vendor's native API protocol | Extension point provided | Small Python `Provider` contract; scripted adapter exercises the runner | Requires a reviewed adapter and its own compatibility tests |

The compatible HTTP adapter sends a non-streaming Chat Completions request with function tools. It expects a single assistant message with string content and/or function `tool_calls`. A model that returns only prose can produce an explicitly unsupported proposal; it cannot manufacture verified citations by inserting citation-looking text in prose. A usable connected model should follow search/read tools and finish with exact quotation/hash citations.

## Local readiness check on 2026-09-06

A targeted, read-only check of the development machine found:

- No `ollama`, `lms`, `lmstudio`, `llama-server`, or `llama-cli` command on the current command path.
- No matching Ollama, LM Studio, llama, vLLM, or text-generation runner process in the targeted process-name check.
- No executable at the checked default Ollama and LM Studio installation paths.
- No default Hugging Face Hub cache directory available to inspect for model names.

These checks did not identify a ready local model server, so no model-list endpoint or synthetic inference trial was attempted. They do not prove that no model exists elsewhere on the machine. No port scan, private cache-content reading, model download, large dependency installation, GPU training, or paid inference was performed for this compatibility pass.

## Reproduce the implemented checks

From the repository with the locked environment:

```powershell
uv sync --all-extras
uv run --frozen pytest tests/test_agent.py tests/test_providers.py tests/test_mcp.py tests/test_agent_app.py
```

The real MCP stdio test launches a synthetic local subprocess using the installed SDK. A restricted Windows sandbox may block its named pipes before the server starts; run that test from an ordinary authorized local terminal. This environmental requirement is distinct from provider connectivity or model quality.

The HTTP integration checks cover the full demonstration-to-draft workflow and reopening; separate human approval; remote refusal without a provider call; local and remote adapter selection; unselected-source exclusion; strict request limits; credential echoes and exceptions absent from state, traces, drafts, events and exports; malicious tool attempts; and malformed model text retained as failed runs. Model transport tests are mocks and must not be described as successful live API requests.

## Evaluate a model before relying on it

Use a new workspace containing only fictional data or material explicitly cleared for the chosen provider. Record the model identifier and version, server version, inference parameters, machine or endpoint class, Scientist OS commit and dependency lock, and source revisions. Start with one short task and a small request limit.

Check that the model can search, read and complete the tool protocol; cite a correct exact passage and hash; distinguish insufficient evidence and contradictions; refuse source-selection escapes and nonexistent tools; preserve uncertainty; and submit an unapproved proposal. Inspect the persisted trace and then reopen the workspace to verify the run and draft. Include failures rather than reporting only successful attempts.

An exact quote proves that text is present in the selected record. It does not prove that the answer follows from the evidence. Assess unsupported assertions, incomplete citations, scientific meaning, and usability separately with a human reviewer. Do not turn one successful synthetic tool trial into a scientific validation claim or a claim of broad model compatibility.

For an MCP host, also inspect that host's available tools and disclosure settings. The harness cannot observe or constrain its unrelated tools, hidden context, other conversations, or model requests. The default bridge requires external disclosure permission because the host's inference location is unknown; `--local-client` is appropriate only when both the host and inference have been verified local.

See [PROVIDERS.md](PROVIDERS.md) for configuration, transport limits, provider adapters, and the MCP source-selection policy.
