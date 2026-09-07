# Security and data boundaries

This is a **single-user local application**. Use the loopback-only CLI. There are no authenticated accounts, lab roles, tenancy, encryption at rest, digital signatures, tamper-proof logs or operating-system sandbox. Programs with access to your account can access its files. Do not expose the server to a LAN or internet.

## Conversational host and execution

The 0.3 host skill invokes the capable host's own tools and the action-capable scientific CLI/MCP interface. It is authorized to operate the application. Startup roots constrain scientific ingestion/execution tool inputs; they do not sandbox the host or a trusted Python program. The host controls inference, permissions, connectors and onward disclosure. Local files and local MCP transport do not prove local inference. Use only explicitly permitted source/code roots and trusted code.

Python runs use a committed code snapshot and copied inputs, with an explicit interpreter/environment, bounded execution and retained manifests/logs/QC. Code can still use ordinary operating-system privileges and network access. Environment filtering and path checks reduce accidental exposure; they are not adversarial process isolation. Do not run untrusted source instructions or executables.

Human scientific decisions are attributed records, not authenticated signatures. Scoped evidence approvals bind scientific source fingerprints and must be renewed when their evidence changes or their decision is superseded. A host tool can record a real supplied decision; it must never impersonate a human. Hosts with direct filesystem access can bypass application checks, so the procedures and scientific lead remain necessary.

## Legacy bounded models

The built-in agent sees selected records only. Before each request it checks revisions, hashes and external-sharing permission. Remote endpoints require HTTPS; redirects are disabled, request/response/time limits apply, and credentials stay in environment configuration. No external fallback occurs. A local server can itself proxy to external services; its egress is outside this harness.

MCP uses fixed startup source selection and defaults to treating its client as external. The local-client option is a human assertion, not network monitoring. External hosts can have separate tools, permissions and context. Scientist OS does not constrain those tools.

Models cannot approve, read arbitrary files, execute commands, fetch URLs, publish or modify original sources through the built-in tools. Imported text remains untrusted. Quote matching establishes source presence/freshness, not semantic support or scientific truth.

## Application and records

Authoring checks the manuscript/discussion's explicit external permission in addition to selected source permissions. Only the selected passage or deliberately included discussion turns enter model context. Proposal application requires the original manuscript revision, unchanged evidence and a named reviewer. A local user may edit records directly; this remains an audit trail, not authenticated authorship.

Project-library uploads are capped at 20 MB. Office XML is parsed with entity protection, bounded archive membership/expansion and active-object rejection; PDFs have bounded structure/text extraction. Extraction is not a hardened operating-system sandbox. Do not use the application as a public upload endpoint. Originals are content-addressed inside the workspace, hashes are checked on download/excerpt creation, and downloads are attachments rather than active inline documents. Scientific plots are generated from trusted registered numeric results, not executed imported SVG.

Crossref discovery runs only on an explicit typed public query. It uses a fixed HTTPS endpoint, disabled redirects/proxies, bounded responses and timeouts. It has no workspace access and never downloads source URLs or restricted full text. Search results and imported documents remain untrusted.

The API rejects unexpected hosts, cross-origin browser requests and writes missing the process request token. The token is not authentication against a local program. Dynamic record text is escaped. Figures use a deterministic renderer with escaped labels. Inputs have explicit limits.

SQLite transactions couple changes and history. Hash chains reveal supported integrity failures but cannot protect against an attacker able to rewrite the whole database. Reviewer names are attributed statements, not authenticated identities. Metadata paths are never opened or copied by the record store.

Exports contain registered text, metadata and agent traces. Check them before sharing. Credential-pattern redaction is a secondary safeguard, not guaranteed detection of all sensitive text. Do not store credentials as research content. Stop the app before backing up its entire workspace directory. JSON is a handoff format; database restore from JSON is not implemented.

## Reporting

Do not post private content or credentials in a public issue. Use GitHub private vulnerability reporting if enabled, or an established private channel to the owner. Supply a minimal fictional reproduction and affected version. No response-time service agreement is offered for this experimental beta.
