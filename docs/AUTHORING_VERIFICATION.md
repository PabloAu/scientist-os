# Authoring beta verification

Version **0.2.0b1**, 2026-09-06. This record describes actual engineering checks,
not scientific validation, human usability research or live-model quality.

| Check | Observed result |
| --- | --- |
| Complete Python suite | **454 passed** in 12.97 seconds on Windows 11 / Python 3.12.0 |
| Static checks | Ruff, both JavaScript syntax checks and Git whitespace checks passed |
| Frontend behavior regressions | **7 passed** using the real browser scripts with DOM stubs: metadata escaping, legacy routing, cached reviews, dirty drafts, UTF-16/CRLF selections and pending-save recovery |
| Real MCP protocol | Included in the full suite; ordinary Windows process/pipe permissions required |
| Clean wheel installation | Passed in a fresh isolated environment importing from site-packages |
| Installed-wheel authoring flow | Seeded manuscript/deck/library; selected-passage proposal and human apply; DOCX/PPTX, original download, exact excerpt, discussion and integrity audit passed |
| Manuscript browser flow | Selected exact passage, requested demo proposal, edited replacement, applied with explicit agent-operated test attribution; revision increased and scientific status remained unreviewed |
| Manuscript preview | All six sections, the loaded figure, numbered reference and supplementary section were observed |
| Presentation browser flow | Inspected result slide, edited speaker notes, saved revision and completed PPTX export |
| Discussion browser flow | Selected evidence, asked a question, observed the persisted turn, citations and optional history selection |
| Literature browser flow | Sent explicit public query to Crossref, inspected results and saved bibliographic metadata without claiming full-text review |
| Project-library browser flow | Imported a generated fictional PPTX; inspected slide-located text; registered an exact selected excerpt with external use blocked |
| Actual Office rendering | Four generated slides rendered with installed PowerPoint and manuscript rendered with Word/Poppler; every rendered page/slide inspected after layout corrections |
| Release contents | Wheel/source allowlists and relative documentation links inspected; no workspaces, attachments, private source clone or credentials included |

The generated Office QA fixture included deliberate literal markup to test safe
text handling. It is private engineering test output, not a scientific manuscript
or a public publication. Office applications are not runtime dependencies.

## Audit findings closed

Independent agent reviews reproduced and helped correct cross-module limits,
long-reference registration failures, malformed metadata, save/export title and
body discrepancies, indirect stale-evidence export, Unicode selection errors and
unsafe reference-year interpolation. Frontend fixes address edits during pending
saves, lost replacement edits, stale cached review state and legacy free-text
manuscript routing. PDF decompression bounds apply before extraction, and the
tests include crafted compression bombs and limit restoration.

The browser import test was initially interrupted by automatic approval review
when the account reached its usage limit. After the user asked to continue, the
same supported browser flow resumed and completed. No alternate browser or
indirect mechanism bypassed that rejection.

## Reproduce and interpret

Run the full suite, frontend check, release inspection and isolated-wheel smoke
workflow described in README and CONTRIBUTING. GitHub Actions checks Windows and
Linux with Python 3.12 and 3.13. Consult the run attached to the exact release
commit for the observed remote result; configuration is not proof of success.

Two upstream test-client deprecation warnings remain. They do not change the
observed pass/fail results. The developer browser tests used fictional research
and the identity **Authoring UI test (agent-operated)**. They are not human
scientific reviews or adoption studies.

Real-model language quality, field-specific scientific suitability, independent
scientist usability, OCR/table extraction, shared hosting/authentication and
signed installers remain unvalidated or unimplemented as documented in the
[authoring guide](AUTHORING_GUIDE.md) and [roadmap](PRODUCT_ROADMAP.md).
