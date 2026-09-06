# Security and data boundaries

This is a **single-user local application**. Use the loopback-only CLI. There are no authenticated accounts, lab roles, tenancy, encryption at rest, digital signatures, tamper-proof logs or operating-system sandbox. Programs with access to your account can access its files. Do not expose the server to a LAN or internet.

## Models

The built-in agent sees selected records only. Before each request it checks revisions, hashes and external-sharing permission. Remote endpoints require HTTPS; redirects are disabled, request/response/time limits apply, and credentials stay in environment configuration. No external fallback occurs. A local server can itself proxy to external services; its egress is outside this harness.

MCP uses fixed startup source selection and defaults to treating its client as external. The local-client option is a human assertion, not network monitoring. External hosts can have separate tools, permissions and context. Scientist OS does not constrain those tools.

Models cannot approve, read arbitrary files, execute commands, fetch URLs, publish or modify original sources through the built-in tools. Imported text remains untrusted. Quote matching establishes source presence/freshness, not semantic support or scientific truth.

## Application and records

The API rejects unexpected hosts, cross-origin browser requests and writes missing the process request token. The token is not authentication against a local program. Dynamic record text is escaped. Figures use a deterministic renderer with escaped labels. Inputs have explicit limits.

SQLite transactions couple changes and history. Hash chains reveal supported integrity failures but cannot protect against an attacker able to rewrite the whole database. Reviewer names are attributed statements, not authenticated identities. Metadata paths are never opened or copied by the record store.

Exports contain registered text, metadata and agent traces. Check them before sharing. Credential-pattern redaction is a secondary safeguard, not guaranteed detection of all sensitive text. Do not store credentials as research content. Stop the app before backing up its entire workspace directory. JSON is a handoff format; database restore from JSON is not implemented.

## Reporting

Do not post private content or credentials in a public issue. Use GitHub private vulnerability reporting if enabled, or an established private channel to the owner. Supply a minimal fictional reproduction and affected version. No response-time service agreement is offered for this experimental beta.
