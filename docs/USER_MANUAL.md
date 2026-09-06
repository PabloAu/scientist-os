# Scientist OS user manual

For the 0.2 authoring workspace, start with the [authoring guide](AUTHORING_GUIDE.md): manuscript sections, passage refinement, references, project documents, PowerPoint and research discussions. The record, analysis and review principles below still apply. **Project**, **Model runner**, and **History & exports** replace the older Overview, Research assistant, and Activity & exports labels.

Scientist OS helps an individual scientist keep evidence, methods, analyses and writing connected. You choose the question, provide the records, decide what a model may see, and review what becomes part of your research. The beta combines a local browser interface, an installable Python application, deterministic scientific tools and an optional model connection.

The first useful project can be small: one experimental question, one protocol, one dataset and one candidate figure. The application does not need a model account for record keeping, calculations, figures, audits or the teaching demonstration.

## 1. Start and reopen a workspace

Follow the [README installation instructions](../README.md) first. From the installed repository environment:

```powershell
uv run scientist-os init --workspace workspaces/my-research
uv run scientist-os serve --workspace workspaces/my-research
```

Open the local address printed in the terminal, normally [http://127.0.0.1:8765](http://127.0.0.1:8765). Keep that terminal running while using the application. Press **Ctrl+C** to stop it. Starting the same command with the same workspace directory reopens the saved records; it does not start an empty project.

The application files and your research workspace are different things. A workspace is the directory containing `scientist-os.sqlite3`. Give different research projects different workspace directories. Use an absolute path when launching from different folders so you do not accidentally create a second project with the same relative name.

If another application uses port 8765, add `--port 8766` and open the printed address. This beta is intended for your own computer. It has no shared-lab accounts, authenticated reviewer identities or public hosting mode.

## 2. Walk through the fictional microscopy example

Use a separate empty workspace:

```powershell
uv run scientist-os serve --workspace workspaces/teaching-example
```

1. On **Overview**, choose **Load the teaching example**. The button is disabled when records already exist to prevent mixing the example with research.
2. Open **Research records**. Inspect the main synthetic study notes, contradictory pilot note, calibration protocol and readings dataset. The records are fictional; no biological experiment or validation occurred.
3. Open **Research assistant**. Keep **Demonstration · deterministic, no LLM** selected. Select the two source notes and ask what they support. Inspect the returned passage and complete tool trail. The demonstration exercises search, read and finish; its fixed response does not reason about your question or adapt substantive scientific advice to your style.
4. Open **Analysis & figures**. Choose **Synthetic fluorescence readings**, **Group summary**, and the columns `signal`, `group`, `day`. Run the analysis.
5. Inspect **Numerical results and exclusions** and the linked analysis record. The control day means are 10, 12 and 11; the treatment day means are 13, 15 and 14. The group means are therefore 11 and 14, with three independent days per group. Two technical readings within a day do not double that sample size. Figure bars show one standard error, approximately 0.577 for each group; they are not 95% confidence intervals.
6. Practice a scoped human review on a source or note. Enter your name and what you checked. Changes to upstream records can invalidate dependent reviews; see the review-order procedure below before approving an analysis and its figure.
7. Open **Evidence audit** to inspect integrity findings and scientific screening separately. Some example records deliberately lack complete scientific metadata. A screening flag is a prompt to investigate, not a finding that the fictional research is biased.
8. Open **Activity & exports** and download the full JSON bundle and readable Markdown report. Neither action publishes anything.

You can also seed a fresh example from the command line using `uv run scientist-os demo --workspace workspaces/teaching-example`. Do that before loading the example in the UI, not afterward. The optional `--domain environment` provides another fictional teaching context; it is not a real environmental dataset.

## 3. Start your own project with checked evidence

Create an empty workspace for actual research. Begin with a **Research note** defining the question, intended audience, decision owner, available evidence and unresolved facts. Use **Register a record** to add each source, protocol, material and dataset needed for the first question.

For a paper or report, inspect the original yourself and register a checked text excerpt. Include the DOI or stable location, page/section/table/figure locator, publication status and any important boundary. For example, record whether the passage is an observation, a hypothesis, an author's proposed method, or a secondary summary. A proposal or slide deck can be useful author context without becoming independent evidence for its claims.

The generic record editor loads UTF-8 `.txt`, `.md`, `.csv`, `.json` and `.tsv` files up to 1 MB into a record's text field. Loading JSON or TSV stores text; it does not automatically interpret a study schema or convert TSV to CSV. The numerical tool expects comma-separated CSV. The separate **Project library** supports original PDF, Word and PowerPoint text extraction and retains their original bytes; see the [authoring guide](AUTHORING_GUIDE.md). Image/video extraction and OCR are not implemented. The application never opens a filesystem path merely because you put it in metadata.

The record SHA-256 identifies the **registered UTF-8 content**. Project-library imports additionally store `attachment_sha256` for the original file bytes; those are distinct hashes. Raw acquisitions and external repositories are not automatically hashed. Record their checksums and how they were obtained when registering them.

### Fields in the record editor

| Field | How to use it |
| --- | --- |
| Record type | Select the scientific role. A saved record's type cannot be changed in the editor. |
| Title | A recognizable label; the application also assigns a stable record ID. |
| Content or source excerpt | Checked source text, protocol, CSV, definition, interpretation or manuscript section. Separate facts from proposed conclusions. |
| Origin / original locator | DOI plus page, repository location, instrument export location or original file and exact passage. Stored as `locator`. |
| Authority | Choose peer-reviewed source, preprint, project observation, author context, synthetic example or unresolved. This is your declaration, not an automatic credential check. |
| Rights / license | Record known rights, internal-use restrictions or `Unresolved`. Access alone does not establish permission to share. |
| Units | Physical/effect units and any transformations; use `dimensionless` when justified, not as a default. |
| Independent unit | Preparation, acquisition day, animal, study or another design-appropriate unit; preserve higher-level nesting. |
| Protocol version | The exact version or immutable revision that applies. |
| Link related records | Select this record's upstream evidence/inputs. Use Ctrl/Cmd to select several. Links are dependencies, not arbitrary bidirectional relationships. |
| External-model permission | Explicitly allow this record to enter a remote-model run. Leave unchecked when permission is unresolved. This is separate from scientific approval. |
| Additional metadata | A JSON object for structured details such as exclusion criteria, software version or citation fields. Use JSON `true`/`false` and double quotes. |

Links must point to existing records. Self-links, missing links and dependency cycles are rejected. For example, link a dataset to its protocol, then an analysis to its dataset. Do not also link the protocol back to that dataset: that would create a cycle. Registration order should follow the direction of the evidence chain.

### Choose the appropriate record type

| Record | Practical contents and useful fields |
| --- | --- |
| **Source** | Literature excerpt, original observation or author context; include authority, origin/locator, rights, publication status and scope. |
| **Dataset** | CSV for beta calculations, or a description/manifest of externally stored data; record units, independence, raw location, exclusions and protocol/material links. |
| **Material** | Reagent, sample or standard identity; manufacturer/catalogue, lot, preparation and unresolved identity facts. |
| **Protocol** | Versioned acquisition or experimental procedure; steps, instrument settings, deviations, version and material links. |
| **Processed data** | What transformation was done, exact inputs, output location, parameters and quality checks; link raw data, protocol and software. This record does not execute processing. |
| **Analysis** | Question/estimand, inputs, method, code, parameters, results and limits. Built-in calculations create this record with numerical output and source revisions. |
| **Figure / output** | Figure/table/video description and lineage. The built-in renderer produces SVGs; other media remain external descriptions/links. |
| **Claim** | One scoped scientific statement with supporting/conflicting evidence and limitations. An analysis being reproducible does not automatically approve the claim. |
| **Term** | Preferred expression, definition, aliases, intended meaning, excluded interpretations and source support. |
| **Experiment plan** | Proposed hypothesis, independent units, controls, randomization, blinding, outcome, exclusions and stopping/failure criteria. |
| **Manuscript** | Article outline, section, caption or response to reviewers; link the claims and outputs used. |
| **Software** | Canonical repository URL, full `code_commit`, environment-lock hash, execution command and code/data schema relationship. |
| **Decision** | Named design or scope decision, rationale, evidence, uncertainty and re-entry criteria. Lifecycle reviews also create decision records. |
| **Research note** | Questions, working interpretations, missing facts or a task brief that does not yet belong in a more specific record. |

Useful extra metadata for an analysis or experiment is:

```json
{
  "randomization": "Acquisition order randomized within each preparation; sequence stored with the protocol",
  "blinding": "Analysis labels blinded until exclusions were finalized",
  "exclusions": [],
  "hypothesis_status": "prespecified",
  "test_used_for_development": false
}
```

Use these values only when they describe what actually happened. An empty exclusion list means none; a blank field means the information is not recorded. Do not copy a method declaration from an example into real research without checking it.

## 4. Analyze CSV measurements without counting technical repeats as experiments

Register a **Dataset** containing, for example:

```csv
condition,preparation,signal
control,C1,9
control,C1,11
control,C2,11
control,C2,13
treatment,T1,12
treatment,T1,14
treatment,T2,14
treatment,T2,16
```

This is synthetic data for illustration. In **Analysis & figures**, choose **Group summary**, then set Value column to `signal`, Group column to `condition`, and Independent unit column to `preparation`. Column names must match the CSV header exactly. The three selected columns must be distinct.

Repeated rows for one preparation are averaged first. Each resulting preparation mean receives equal weight, even when preparations have different numbers of technical readings. The function reports the number of rows and units, missingness, SD across unit means and standard error. Without an independent-unit column, it reports descriptive row statistics and withholds standard errors. With one nonmissing independent unit, uncertainty is unavailable.

The same unit cannot occur in multiple groups. A paired design, repeated follow-up or shared preparation across treatments requires an appropriate external analysis. Do not rename the units merely to make the restriction disappear. If cells share wells, preparations or days, choose the independence level required by the experiment; the app cannot infer it.

Only empty numeric cells are treated as missing and explicitly excluded. `NA`, `NaN`, infinity, text, malformed numeric values and inconsistent rows stop the calculation. Convert nonempty missing-value codes deliberately and document that preprocessing. No imputation or automatic outlier removal occurs. Review missingness by group: successful parsing does not make missing data ignorable.

The calculation stores numerical results, parameters, input revisions/hashes, software/Python versions and a linked SVG output. Review the result before interpreting its figure. All-missing input or an unsupported plot size may fail the combined analysis-and-figure action; use an appropriate subset or inspect the data directly. The pure Python functions expose their separate results and limits in [Scientific methods](METHODS.md).

## 5. Combine human-checked study-level estimates

The meta-analysis tool accepts a CSV with exactly these required columns: `study_id`, `effect`, `standard_error`. Use the optional `independence_id` when reports share a cohort or experimental population:

```csv
study_id,effect,standard_error,independence_id
Synthetic-A,0,1,Population-A
Synthetic-B,2,1,Population-B
Synthetic-C,4,1,Population-C
```

In **Analysis & figures**, choose **Meta-analysis**, choose fixed effect or random effects, describe the common effect measure including scale/direction/units, and confirm that you checked comparability and independence. The example above is mathematical, not extracted research. With random effects it produces an estimate of 2, `Q=8`, `I2=75%` and `tau2=3`.

Each row must contain a human-checked effect and its correctly derived, positive standard error. Study IDs and independence IDs must be unique. Omitting the optional independence column uses the study ID as the declaration; it does not verify independence. If the column is present, fill it for every row. Different report IDs do not eliminate overlapping participants or shared controls.

The app does not extract effect sizes from prose, convert measurements to a common scale, calculate standard errors from p-values, or decide which studies qualify. For a ratio measure, provide an appropriate transformed estimate and matching standard error, such as a log ratio; the tool does not guess the transformation or exponentiate the answer. Record eligibility criteria, literature search scope and exclusions separately.

Fixed effect uses inverse-variance pooling. Random effects uses the DerSimonian–Laird method. Forest bars are 95% normal intervals. They are not prediction intervals and may understate uncertainty, particularly with few studies. Shared controls, repeated outcomes, hierarchical effects, advanced small-sample methods and publication-bias analysis require another method. See [Scientific methods](METHODS.md) before substantive use.

The assistant task **Plan an evidence synthesis** is different: it proposes a plan from selected records. It does not execute this numerical calculation.

## 6. Work with the assistant and your chosen model

Open **Research assistant**, select a task and only the records needed for that question. Source records may be checked initially; inspect the entire selection before every run. Unselected records and previous runs are not silently added to the model's context. If a previous proposal matters, save it as a record and select it deliberately.

Use **Voice and guidance** to request a style and working scope, for example:

> Use concise, active scientific prose. Separate measured observations from interpretation. Use the selected terminology definitions. Mark unavailable values as unresolved. Explain conflicting evidence and give me two practical follow-up options with the decision each would resolve.

The available tasks cover evidence questions, support/bias audit, experimental proposals, synthesis planning, article drafting, terminology, journal shortlists and figure plans. All are proposals. No task automatically browses literature, runs scientific code, executes an experiment, creates a Git commit, submits an article or approves a record.

| Connection | What to expect |
| --- | --- |
| **Demonstration** | A fixed deterministic tool loop, with no LLM or model bill. Use it to learn the interface and traces. |
| **Configured local model** | A separately installed compatible inference server; its model generates proposals. Scientist OS does not install or launch that model. |
| **Configured remote API** | A compatible HTTPS service; every selected record needs external-model permission. Your provider may charge for requests. |
| **MCP host** | Your external assistant supplies inference and calls the selected-record harness. The host's other tools/context are outside Scientist OS's control. |

Follow [Connect your model](PROVIDERS.md) for environment variables, actual model identifiers, local endpoint policy, MCP configuration and adapter examples. A configured-model option appears after the server has a base URL and model configured. Restart the server after changing its configuration. Not every model supports the required function-call protocol; compatibility and answer quality need testing with the endpoint you select.

The runtime allows at most eight model steps, 16 selected records, 24,000 characters per record and 60,000 selected characters in total. Questions may contain 8,000 characters and style guidance 2,000. Use a coherent, checked excerpt with an original locator when a source is too large. Do not remove context needed to understand a limitation merely to fit a limit.

After a run, inspect the answer, source passages and tool trail. A matching quote/hash establishes that the text occurs in the selected registered content. It does not establish that the conclusion follows from it. An answer can quote a real passage and still overstate causation, ignore a contradiction or invent an unsupported numerical interpretation.

Choose **Save an unreviewed draft** to store a completed proposal as a note, claim, experiment, term, manuscript or decision. Save each run once, then edit that draft. Human corrections to the question or evidence are new explicit runs; there is no hidden chat memory. A failed run preserves its error/trace and cannot be saved as a completed draft. If a selected source changes, start again against the current revision.

## 7. Review in dependency order

Every new or edited record begins **unreviewed**. A human can approve a revision for its stated use or reject it with an explanation. Enter your name and a note describing evidence checked, scope and remaining limitations. Reviewer names are attributed text in a single-user app, not authenticated signatures or proof of independent review.

Review is intentionally conservative. Editing content, title or metadata changes a record revision and invalidates downstream review states. **Reviewing an upstream record also changes its revision**, even when its content hash stays the same. Existing derived outputs may therefore become stale after an approval. The application preserves those records and their history; it does not silently rewrite their evidence.

Use this order for a calculation you intend to rely on:

1. Finalize and review the materials and sources; then the protocols that depend on them; then the dataset and its provenance.
2. Run the calculation against that current dataset revision. Inspect numerical output, unit choices, exclusions, parameters and limitations.
3. Review the **Analysis** record. This makes the automatically created draft figure stale because it referred to the analysis revision before review.
4. Use **Regenerate linked figure** on the analysis record to create a new figure bound to its current revision. Inspect and review that new figure. Keep the earlier figure as historical output.
5. Create/review claims that use the reviewed analysis and figure. Create/review manuscript sections after their source claims are stable. Record lifecycle reviews after the records they depend on are finalized.

If a figure is reported stale or cannot be displayed, examine its linked analysis and data. Regenerate the figure after an analysis review; rerun the analysis after a dataset change. A source edit cannot be repaired by approving a stale analysis or merely changing its recorded input revision. If an externally executed analysis remains valid after a metadata-only change, a human must explicitly reconcile and document the relationship rather than pretending the computation was rerun.

No deletion is available in the beta. Reject or mark an obsolete record as superseded with a clear note; create the replacement in a way that preserves acyclic lineage. Exports retain old records and events, including earlier text revisions. This history is useful for scientific continuity and matters when deciding what can be shared.

## 8. Practical writing and research patterns

### Build a terminology dictionary

Create one **Term** record per controlled concept. Put the definition and scope in Content, link evidence, and use extra metadata such as:

```json
{
  "preferred_term": "independent experimental unit",
  "aliases": ["unit of independence"],
  "avoid": ["independent frame"],
  "scope": "Define the actual unit from the experiment; do not infer it from a filename"
}
```

Select these term records when asking for manuscript text. Review changes to meanings as scientific decisions. The beta stores and retrieves the dictionary; it does not automatically enforce every occurrence across an article.

### Register a protocol and propose a follow-up

Keep the protocol's actual steps and exact version in a **Protocol** record. Link it to material records, then link the dataset to that protocol. Record a deviation in the dataset or create a new protocol version when it changes the reusable method. Keep missing instrument settings explicitly unresolved.

For a follow-up, select the relevant protocol, observations, contradictory evidence and current limitations. Ask the assistant to propose controls, independent units, blinding/randomization, measurements, exclusions and the result that would falsify the hypothesis. Save the response as an **Experiment plan** and edit it before review. The assistant has not performed the experiment or obtained an ethics/resource approval.

### Associate GitHub software with data and the article

Create a **Software** record with the canonical repository URL in the locator and the full immutable Git commit in additional metadata `code_commit`. Obtain the real commit from the repository; a branch name, `latest`, short hash or copied folder is insufficient. Also record the environment-lock hash, configuration, command, input/output schemas and whether the checkout had local changes when the analysis ran.

Link processed-data/analysis records to that software and the exact datasets, then link outputs and manuscript sections downstream. The application tracks these associations. It does not push commits, open pull requests, clone arbitrary repositories or verify that a commit has been publicly released. Carry out those actions in GitHub or an appropriately authorized external tool and record the actual result.

### Draft an article that stays within its evidence

Start a **Manuscript** record with a journal-neutral outline: question, main finding candidates, methods, evidence for each result, discussion, limitations and availability statements. Link the underlying claims and figures. Ask **Draft article text or structure** to work on one section at a time using the selected evidence and terminology.

Request clear scientific prose, concrete verbs, explicit uncertainty and placeholders for missing facts. Review every number and citation. Avoid treating a polished paragraph as a completed analysis. Save the draft as a manuscript record, edit it directly and review it after its dependencies are stable. The beta displays text and exports Markdown; it does not create a formatted Word manuscript, manage a bibliographic reference database or generate tracked changes.

For **Develop a journal shortlist**, first register current official scope and author-instruction excerpts with dates and URLs. Supply your audience, article type and constraints. A model can compare those selected sources; it has no built-in live journal database and cannot reliably supply current fees, rankings or requirements without evidence.

### Respond to peer review

Preserve the exact submitted version and reviewer requests in authoritative storage. Register a source or note for each request and a decision explaining whether it requires clarification, reanalysis, an experiment or a justified limitation. Link revised manuscript records to the evidence and decisions used. The lifecycle provides review checkpoints; automated response matrices, redlined Word files and submission packaging are outside this beta.

## 9. Use the research lifecycle as a decision record

**Research lifecycle** provides fourteen stages: framing; evidence inventory; materials/protocols; literature mapping; terminology; prespecified analyses/experiments; analysis provenance; bias/claim audit; synthesis; article/journal planning; figures; writing; release handoff; and peer-review response.

Select a stage, inspect every checkpoint, link the relevant records, and write a named decision with scope and unresolved limits. The app saves an approved **Decision** record representing your assessment. It does not test that the entire research project meets a universal scientific standard, force you through every stage in order, or automatically execute work when a box is checked.

If a stage does not apply, explain why in the decision; do not imply work was completed. If assumptions or sources change, revisit the narrowest affected stage. Include relevant evidence links so later changes can invalidate its review state. The stage list is a starting framework; tailor your questions, record content, metadata and decision notes to your field.

## 10. Interpret audits and preserve failures

**Evidence audit** separates two checks:

- **Integrity checks** inspect record hashes, dependency revisions, quotations and audit history. A mismatch or stale input requires correction or recomputation before reliance.
- **Scientific screening** highlights missing provenance, units, independence, protocol versions, immutable code revisions, study-design declarations and potentially unsupported/causal language. These are bounded rules, not a formal risk-of-bias assessment or proof of misconduct.

Follow each finding to its record. Add missing facts only from an appropriate source. If something is unknown, record that uncertainty instead of filling the field to make the dashboard green. Keep negative results, exclusions, failed analyses and deferred evidence visible. Absence of flags means only that the configured rules found none.

The command-line equivalent is `uv run scientist-os audit --workspace workspaces/my-research`. Its nonzero audit exit status identifies integrity findings; scientific screening remains part of the displayed report and human review.

## 11. Export, back up and share deliberately

**Activity & exports** shows recent events and offers:

- **Full JSON bundle:** current records, event history, assistant runs, schema version and integrity manifest.
- **Readable Markdown:** current record contents, metadata, hashes, review states and audit findings. It is not the complete run/event history.

Exports include registered research text and metadata; JSON also includes historical content in events and model traces. Review the complete content before sharing. Source locations, unused results and earlier draft text can be sensitive even when the latest manuscript is public. No export automatically publishes to GitHub, a journal or another service.

For a restorable backup, stop the application and any MCP process using that workspace, then copy the **entire workspace directory** to a new location using your normal backup tool. Reopen the copy with `scientist-os serve --workspace <copied-directory>` and run its audit. Keep the original backup intact while checking a copy. Do not copy only selected database files while a process is writing them.

JSON is a portable handoff, not an import/restore format in this beta. Reopening the complete workspace folder is the supported continuity path. Include its `attachments/` directory: original imported documents are stored there and are not embedded in JSON. Back up externally referenced images, raw acquisitions and code separately: a recorded path is not a copy. An app upgrade should be preceded by a stopped-workspace backup; unknown database schema versions are refused rather than silently migrated.

The generic application uses Apache-2.0. That does not change the license or confidentiality of your imported sources, figures, datasets or manuscripts.

## 12. Troubleshooting and practical limits

| Symptom | What to do |
| --- | --- |
| Workspace appears empty | Check the `--workspace` path and current directory. Stop before investigating; do not load the demo into what should be your real workspace. |
| Example button disabled | It requires an empty workspace. Create a separate teaching workspace. |
| Refresh this page before saving | The server may have restarted and the local browser token changed. Refresh and reopen the current record before editing. |
| Stale revision/input or HTTP 409 | Another edit or review changed an upstream record. Refresh, inspect the change, and rerun/reconcile the dependent work. Do not blindly repeat an old save. |
| Figure becomes stale after analysis review | Regenerate it from the current analysis, then review the new output. If data changed, rerun analysis first. |
| CSV calculation rejects the file | Check exact column names, duplicate headers, row widths, empty group/unit labels, decimal numbers, nonfinite values and study independence IDs. Do not silently drop offending rows. |
| No uncertainty bar | Independent units may be undeclared, fewer than two units may remain, or variation may be exactly zero. Inspect the result, not just the graphic. |
| Configured model is absent | Set the model/base URL in the launching server environment and restart. Follow the provider guide. |
| Windows reports the launcher is in use during upgrade | Stop the running application and MCP processes, then retry installation. Back up stopped workspaces before upgrading. |
| External disclosure refused | A selected record is not explicitly permitted. Narrow the selection or obtain a justified owner decision; do not change the setting merely to suppress the error. |
| Selection/step limit reached | Use a smaller coherent question and selected excerpts, or begin a new explicit run. The runtime caps eight model steps and 16 source records. |
| Invalid provider response or unsupported answer | Check that the endpoint/model supports the documented function-tool protocol. Inspect the preserved trace; a model response is not necessarily a completed citation-checked proposal. |
| Citation or source changed | Reinspect the original and registered excerpt, then run again. Old quotations are not silently promoted to the new source revision. |
| Unknown schema/database-integrity error | Stop, preserve the workspace and backup, record the version and error, and obtain support. Do not reset database versions or modify event tables manually. |

The generic text editor is limited to 1 MB; Project library imports support 20 MB originals with separate extraction bounds. Model selections have smaller character limits, so create explicit excerpts for long documents. Figures support up to 200 groups/studies in the analysis view; Office slide layouts have tighter bounds and reject crowded figures. Large imaging data, hierarchical modelling, arbitrary code execution, OCR/table reconstruction, multi-user hosting and autonomous publication remain outside this beta. Crossref discovery and native PDF/Office text import are explicit user actions.

Use [Scientific methods](METHODS.md), [Model connections](PROVIDERS.md), [Architecture](ARCHITECTURE.md) and [Evaluation protocol](EVALUATION_PROTOCOL.md) when you need the exact assumptions, extension contract or evidence behind a capability.
