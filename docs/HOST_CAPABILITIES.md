# Host capability matrix

Checked 7 September 2026. This distinguishes observed host capabilities from
portable software support. It is not a claim of identical behavior across models.

| Capability | Current local Codex host | Portable core / other hosts |
|---|---|---|
| Conversation and authorized model inference | Current assistant plus independent live host-agent acceptance work; no scripted provider used as conversational proof | Host supplies inference; exact hidden context, usage and backend model identity are not observable to the core |
| Local Python and Git | Executed on Windows/Python 3.12; installed Codex CLI reports 0.153.4 | Python >=3.12; host needs command tools and explicit permissions; Linux unit support is separate from live-host testing |
| Local plugin discovery/install | Personal plugin `scientist-os@personal` installed with official local CLI | Standard skill package; other hosts' discovery/install paths untested |
| Scientific operations | CLI catalog and real create/read/update/ingest/run/edit/export workflows | Same Python service API, no raw model-provider dependency |
| MCP | Real local stdio client initialized and invoked the action interface | Optional MCP extra; not a reasoning runtime, host-UI proof or implicit credential transfer |
| Browsing literature | Current web tools searched and opened original PLOS methods papers and official host docs | Host-dependent; core retains traceable source records and search scope, not an autonomous browser |
| Original visual inspection | Local PDF page and Office-rendered slide inspected in the host | Core preserves originals/extraction states; suitable renderers/vision must be available |
| Editable artifacts | DOCX/PPTX/SVG/HTML generation; actual output rendering required per artifact | Existing Python authoring services plus relevant host artifact tools |
| Native preview and selection | Codex file-preview tool accepts local artifacts; exact-passage edit API tested | No dependency on MCP Apps embedding; native app UI availability is host-specific |
| Durable project continuity | Canonical records, action journal and exported context; fresh-context recovery is separately reported | Project state portable; proprietary transcript and hidden reasoning do not transfer |
| Agents and orchestration | Disjoint development agents and a separate live scientific journey agent | Shipped scout/worker/coordinator procedure; requires host delegation and actual handoff checks |
| External connectors | GitHub metadata/remote verified and permitted branch push exercised | No token inheritance; Google Drive tools present in this host but not exercised for these journeys |
| Arbitrary scientific software | Trusted versioned Python module/script execution exercised | Not a sandbox; no automatic environment installation, GPU allocation or paid compute |
| Other host/model adapters | Not tested in this prototype | Claude/OpenCode/API-only/local-model parity remains untested; use capability checks and declare reduced scope |
| Hosted multiuser application / MCP Apps UI | Not claimed | Future integration, not required for current local conversational route |

The short compatibility check used the installed tools and current official
[plugin instructions](https://learn.chatgpt.com/docs/build-plugins) and
[artifact viewer documentation](https://learn.chatgpt.com/docs/artifacts-viewer).
An installed plugin contributes procedures/tools to capable new conversations;
it does not reproduce every desktop capability inside a raw SDK.

Scientific browsing demonstration consulted
[Lazic et al. 2018](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.2005282)
and the subsequent [population-sampling discussion](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.2007054).
Our inference for the prototype is deliberately bounded: declared units and unit
means help expose pseudoreplication, but design/population dependence can require
a more appropriate hierarchical analysis. These are methodological sources,
not inputs to the fictional effect-size meta-analysis or evidence for the phantom.
