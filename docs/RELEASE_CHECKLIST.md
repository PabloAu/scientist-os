# Beta verification record

Version: 0.1.0b1. Date: 2026-09-06.

This record describes the packaged beta and its completed local checks. No live-model quality, biological validation, independent human annotation, hosted deployment, or public user adoption is implied.

## Measured local results

| Check | Observed result |
| --- | --- |
| Full suite, Windows 11 / Python 3.12.0 | **318 passed** in 9.15 seconds; two dependency deprecation warnings |
| Ruff | Passed for source, tests and release scripts |
| JavaScript syntax | Passed with Node |
| MCP | Real SDK stdio initialize/list/read/blocked-action/proposal flow passed on the normal host |
| Source/wheel build | Passed with Hatchling 1.32.0; explicit package allowlists inspected |
| Clean wheel installation | Passed in a fresh environment; imported from site-packages, not editable source |
| Installed-wheel workflow | UI assets, fictional demo, three-request agent run, unreviewed draft, means 11/14, exact SVG bytes, JSON/Markdown export and reopen passed |
| Browser workflow | Inspected overview, selected-source run, grounding warnings, draft save, named review dialog, calculation and figure; declared n=3 units/group and SEM 0.57735 observed |
| Scientific fixtures | Known-answer numerical tests; fictional supported/contradictory/unknown/stale retrieval cases; no model-quality score |
| Preserved source clone | Clean at original revision 00273003a5154672583888c6993751ad463f977e |

The browser review action used the explicit test identity **Beta UI test (agent-operated)** and fictional evidence. It is an interface test, not a human scientific review or adoption study. The example used for the final preview starts separately from those test records.

The clean-install check is reproducible with `scripts/smoke_install.py` using an isolated interpreter that has installed the wheel and its dependencies. Package hashes are distributed alongside the exact release assets in SHA256SUMS.txt; they are not embedded recursively in this source archive. The lockfile hash and installed dependency metadata are recorded in [DEPENDENCIES.md](DEPENDENCIES.md).

## Continuous integration

GitHub Actions is configured for Windows and Linux on Python 3.12 and 3.13. Its observed remote result is recorded in the GitHub run attached to the release commit; configuration alone is not evidence of a passed run.

## Release scope

- Generic Python product with fresh Git history; private source clone ignored.
- User authorized Apache-2.0 for generic code/workflows; original fictional fixtures use CC0-1.0.
- Local, single-user installation and browser UI; optional model APIs and MCP.
- No source-project scientific records, documents, images, private paths or history in the product allowlist.

## Completed engineering evidence

The source audit reproduced legacy packet-directory traversal and unverifiable worker attestation in an isolated copied helper with fictional inputs. The original source and its clone remained unchanged.

Core and integration checks include malformed inputs, path-like IDs, exact citations, stale direct/indirect lineage, human-only approval, transaction rollback, concurrency, interrupted/nested failures, source disclosure revocation, invalid model output, credential echoes, safe SVG content, API-origin controls, persistence, backup/reopen and JSON/Markdown export. MCP includes a real SDK client/server round trip, not only mocks.

The statistical tests use declared synthetic known answers. See [METHODS.md](METHODS.md) and [EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md). No held-out real-model score or human assessment was produced.

## Known limits

- Live model servers and specific model behaviors remain unvalidated; see [MODEL_COMPATIBILITY.md](MODEL_COMPATIBILITY.md).
- No public multi-user hosting, authentication, PDF/OCR pipeline, arbitrary code execution, automated literature acquisition or publication.
- A stale figure is rejected until recomputed/rebound. Reviewer names are asserted locally, not authenticated.
- Dependency test-client deprecation warnings remain; execution results determine pass/fail.
- Stop a running Windows console launcher before reinstalling/upgrading the package; the operating system can lock its executable. This was encountered and resolved during packaging, then the full suite and clean installation passed.
- This is an engineering-tested experimental beta for user trials, not a claim of production readiness or scientific validation.
