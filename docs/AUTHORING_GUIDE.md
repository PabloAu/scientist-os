> Historical v0.2 browser/bounded-provider documentation. For the current conversational prototype, start with [the host manual](CONVERSATIONAL_MANUAL.md) and [0.3 verification](PROTOTYPE_VERIFICATION.md).

# Write, discuss and present

Scientist OS 0.2 adds a working authoring studio to the evidence workspace. It is a
single-user local application. Each save creates a revision; applying a model edit
records your decision but does not approve its scientific validity.

## First walkthrough

Use a new workspace for the complete fictional example:

```sh
uv sync --frozen --all-extras
uv run scientist-os demo --authoring --workspace workspaces/writing-example
uv run scientist-os serve --workspace workspaces/writing-example
```

Open the local address printed by the application. The example contains a
manuscript, figure, reference, four-slide presentation, project note and discussion
topic. Every scientific statement in it is explicitly fictional. To begin real
work, create a separate workspace with `scientist-os init`.

Existing 0.1 workspace records remain readable. Back up the entire stopped
workspace before upgrading. The new editor identifies structured manuscripts by
their sections; an older free-text manuscript remains available in Research
records. Create a new structured manuscript and copy its text into sections to
adopt the new workflow while preserving the original record.

## Compose a manuscript

Open **Manuscripts**, create a manuscript, and choose a section. Start with Abstract,
Introduction, Methods, Results, Discussion and Supplementary material, or arrange
sections for your article type. Change headings, add sections and reorder them.
Text is plain text with paragraph breaks. The manuscript canvas assembles the
saved/draft text and registered figures into a readable paper view; it is not a
publisher-specific typesetting engine or a general Word layout editor.

Attach figures and references to their relevant sections. Only registered,
reproducible figures are supported in this beta. A figure remains linked to the
analysis and input revisions that produced it. Mark supporting sections as
supplementary; they remain visible and appear in exports. Reference numbers are
assembled from the linked reference records rather than invented by the model.

Save before asking the assistant to work on a passage. Each section has a stable
identifier, but a save creates a revision of the whole manuscript. This protects
against competing tabs overwriting one another. If a revision conflict appears,
keep a copy of any unsaved text, reload the current version and reconcile your edit.
Unsaved-change prompts protect navigation; they are not a substitute for saving.

### Refine a passage or check its provenance

1. Select text in the section editor. The selected passage is captured before you
   move focus into the assistant instruction field.
2. Choose the evidence records the model may read. For long documents, first make
   an excerpt in Project library. Include contrary findings and limitations.
3. State a narrow request, for example: “Rewrite this result in concise scientific
   prose. Keep all values, units and uncertainty. Do not imply causation.” Or ask:
   “Check each claim against these sources. Identify missing or conflicting support.”
4. Choose the deterministic demonstration or a configured model. Add style guidance
   such as preferred terminology, voice or journal conventions.
5. Inspect the returned proposal, exact quotations, warnings and source trail.
   You may edit the proposed replacement before applying it. An audit response is
   advice to inspect; do not insert audit findings into prose unless that is intended.
6. Apply only the text you want, with your name and an optional decision note.
   Nothing is applied automatically. The manuscript remains scientifically unreviewed.

Only the passage, your instruction/style and explicitly selected evidence enter
the model request. The rest of the manuscript does not enter implicitly. External
models also need explicit permission for the manuscript context itself. Sharing
permissions and source revisions are checked before each model request.

A changed manuscript, changed selected source, or stale ancestor blocks application.
Generate a new proposal after checking the new evidence. Acceptance records remain
in history; later source changes cannot silently keep old prose “verified.” Exact
quotation matching establishes traceability, not semantic support or scientific truth.

The demo uses the real bounded tools without an LLM. It returns a labelled teaching
response, not a polished rewrite. Connect a tool-capable model using the
[provider guide](PROVIDERS.md) for real language generation. No model quality is
guaranteed by transport compatibility.

## Maintain references and read literature

In **References**, create bibliographic entries with title, authors, year, journal,
DOI, URL and an optional abstract. Link separately imported full text where you
have lawful access. A bibliographic entry or supplied abstract does not establish
that the complete paper was read or that its claims are reliable.

The optional Crossref search sends only your explicitly typed public query to
Crossref. It returns at most five publisher-deposited metadata entries. Inspect
and deliberately save the entries you want; no query is generated from private
project content and no record is imported automatically. Oversized or malformed
abstracts are omitted rather than silently shortened. Search ranking is neither
an assessment of evidence quality nor a comprehensive systematic review.

For field-direction discussions, select the relevant paper excerpts, current
experiment records and recent decisions. A model has no implicit access to the
latest literature. Search and import additional literature when the supplied
evidence is insufficient. Current journal requirements need dated official sources.

## Bring project documents into the library

**Project library** accepts original PDF, DOCX, PPTX, TXT, Markdown and CSV files,
up to 20 MB each. Choose a useful category such as paper, proposal, presentation,
protocol or notes. Registration preserves original bytes under their SHA-256
identity. Downloading the original checks those bytes against the stored hash.

The preview contains extracted text with page, slide, paragraph or line locators.
Office files are read as data; macros, linked content and embedded objects are not
executed. PDFs use their native text layer. Scanned pages require an external OCR
workflow; equations, tables, layout and reading order can be incomplete. Inspect
the original when scientific interpretation depends on those details. An empty or
failed extraction must not be treated as evidence that the document says nothing.

Long documents often exceed a model run's per-record bound. Select the relevant
passage in the extracted-text view and register an excerpt. This creates a source
record with the exact text, source revision/hash and selection location. No silent
truncation or automatic model upload occurs. Excerpts inherit a dependency on the
registered original; updates make their provenance stale until checked again.

Imported documents are private to the local workspace by default. Review their
metadata before allowing an external model to read a document or excerpt.

## Build a professional presentation

Open **Presentations** and create a deck, or open the teaching deck. Add and reorder
slides; edit title, body, speaker notes, references and the registered figure.
The four layouts are title, section, evidence and two-column. The design uses a
restrained navy/white palette, clear alignment and generous margins.

Use one scientific message per slide. For example, title a result with a specific
finding, show the corresponding figure and units, and put caveats in the body or
speaker notes. Keep a clear distinction between observations, proposed experiments
and conclusions. Use Discussions or Model runner to develop an evidence-backed
outline, then inspect and copy the selected prose into the slides.

The slide preview uses current registered content. PowerPoint export produces
editable text and shapes, including editable scientific plot elements. Reference
details, record revisions and provenance appear in speaker notes. The browser
preview is a content/layout aid, not a pixel-identical PowerPoint renderer.

Dense content is rejected rather than silently cut off. Shorten it, split it into
more slides or move detail to notes. Scientific figure labels and units are retained;
unsupported/crowded plots need a more suitable layout or a smaller figure.

Exporting does not imply approval. Changes to linked data, analyses, figures or
references can make the deck stale. Regenerate the affected analysis/figure,
inspect it, replace the linked figure and save the deck before exporting again.

## Discuss directions and alternatives

Create a topic in **Discussions**, describing the question or perspective to
explore. Select current experiment, progress, analysis and literature records.
Ask about alternative interpretations, controls, missing evidence or the next
experiment. Include your name so the transcript records who asked the question.

Past turns remain visible, but they are not silently included in the next model
request. Explicitly select prior turns when useful. Their original evidence must
be reselected and unchanged. Earlier assistant text is unreviewed conversation,
not a new scientific source. Each model turn retains its run, citations, warnings
and source snapshots. Failed runs are visible and do not become successful answers.

To make a direction into a project decision, register an Experiment or Decision
record, link its evidence and perform the ordinary named human review. A discussion
alone neither executes an experiment nor updates a protocol.

## Export, back up and recover

Manuscripts export to editable DOCX and standalone HTML with figures, references
and supplements. Presentations export to PPTX. Exports report the current review
state and preserve source context; they do not submit or publish anything.

Use **History & exports** for the JSON evidence handoff and readable Markdown
report. These exports do not contain original attachment bytes and are not full
workspace backups. Stop the server and copy the entire workspace directory,
including `scientist-os.sqlite3` and `attachments/`, for restoration. Reopen the
copied directory with `serve --workspace`.

Record history retains prior versions. There is no destructive delete or automatic
restore-from-JSON operation in this beta. If a source changed, inspect the audit
finding and rebuild dependent work. Do not clear hashes or reviews merely to
silence a warning.

## Practical bounds

| Item | Bound |
| --- | --- |
| Manuscript | 40 sections; 120,000 aggregate text characters |
| Passage request | 5,000 selected characters; 2,000 instruction characters |
| Selected model evidence | 16 records; 24,000 characters per record; 60,000 in total |
| File import | 20 MB original; bounded archives/pages/extracted text |
| Document excerpt | 20,000 characters, exact selection |
| Presentation | 40 slides; layout-specific title/body density limits |
| Discussion | 50 turns; question 3,000 characters; up to 5 prior turns and 3,000 characters of history |

See [verification](RELEASE_CHECKLIST.md), [scientific methods](METHODS.md),
[studio contracts](STUDIO_CONTRACT.md) and [publishing contracts](PUBLISHING_CONTRACT.md)
for implementation and evidence details. This is an engineering-tested experimental
beta; scientific model quality and real scientist usability remain separate evaluations.
