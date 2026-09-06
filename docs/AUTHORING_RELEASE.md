# Authoring beta scope

Target version: 0.2.0b1. This brief captures the requested behavior and is the basis
for implementation review. Completed verification is recorded separately in
RELEASE_CHECKLIST.md.

## Scientist workflow

1. Import permitted project documents, presentations, proposals and articles. Keep
   original bytes and a hash; view extracted text with locators and extraction limits.
2. Maintain a reference library. Enter bibliographic details or explicitly search
   Crossref, inspect results, and save selected entries. Bibliographic metadata is
   distinct from a read paper; full text must be imported and deliberately selected.
3. Compose a manuscript section by section. Reorder sections, attach registered
   figures and references, and include supplementary sections. See the assembled
   manuscript and export editable Word or standalone HTML.
4. Select a passage, request a refinement or provenance check with chosen evidence,
   inspect the proposal and citations, edit it if needed, and explicitly apply it.
   Applying must reject a changed manuscript or stale evidence and record attribution.
5. Build a presentation slide by slide, using current figures, experiments and ideas.
   Preview the presentation and export an editable, restrained professional PPTX with
   source details. Save/reopen retains slide order, content, notes and linked evidence.
6. Discuss directions, hypotheses and perspectives in persistent threads, selecting
   current project evidence and published-literature excerpts. Deliberately include
   prior turns; no implicit private history or claim of comprehensive field knowledge.

## Product requirements

- Preserve the existing records, analyses, human reviews, agent provider neutrality,
  lifecycle gates, audit and exports.
- Keep the current single-user local application model, no paid model calls.
- Clear selection scope, busy/error states, revision conflicts and unsaved-edit handling.
- Restrained navigation, strong typographic hierarchy and a readable paper canvas;
  no decorative chat mascots, sparkle icons or stock dashboard decoration.
- Retain synthetic examples and honest distinctions between demo, live model output,
  engineer verification and scientific validation.
- Audit extraction/file boundaries, figure/reference freshness, edit application,
  source disclosure, persistence, package installation and end-to-end UI behavior.

## Design references

The UI direction draws on [Linear's explanation of hierarchy and restrained navigation](https://linear.app/now/how-we-redesigned-the-linear-ui)
and [Overleaf's explicit text selection and commenting workflow](https://docs.overleaf.com/collaborating/commenting).
These inform interaction choices; no third-party UI assets are copied.
[Crossref's REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
defines the bibliographic discovery source and its scope. Search is explicit and
sends only the scientist's typed query, not manuscript or workspace content.
