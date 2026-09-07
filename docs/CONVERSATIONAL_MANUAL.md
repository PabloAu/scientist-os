# Scientist OS conversational manual

Scientist OS runs inside your capable assistant. Talk about the research, point to
permitted sources, select an artifact, and ask for work. The installed skill supplies
the scientific procedures; Python tools preserve records and execute analyses.
The old browser application is an optional inspection/editor surface. Its selected
text answer generator is not the conversational runtime described here.

## Start a project

Install the Python package and host skill using [installation](HOST_INSTALLATION.md).
In a new Codex conversation, invoke **Scientist OS** and say, for example:

> Use Scientist OS in my selected research folder. I am investigating whether an
> imaging correction improves measurement precision. Help me frame the question,
> incorporate the folders I identify, and keep our evidence and decisions organized.

The assistant can start with no evidence records. It should ask about scientific
facts that matter, retain unknowns, and make progress on independent work. Tell it
which folders it may inspect and whether material is private, published, licensed,
owner-described experimental data or a plan. Access alone does not grant release
rights. Local storage can be used with remote host inference: use your host's
disclosure settings and approved source scope.

Routine authorized operations can proceed without repeated confirmation. Changing
the scientific estimand, choosing an exclusion, approving a central claim, committing
resources to experiments, or changing governance needs the scientist's decision.
The software attributes a decision; it does not authenticate that person's identity.

## Supply mixed sources

Say “Scout and incorporate this folder.” The assistant inventories files and sizes,
selects coherent work, preserves original bytes, registers locators/hashes, and
retains gaps. It can use host agents in disjoint lanes under the supplied procedure.
The coordinator checks the handoffs and integrates the records.

The core extracts native PDF text, Word paragraphs, PowerPoint slide text and UTF-8
text/CSV. It preserves unsupported formats as inert attachments with explicit gaps.
Each file is limited to 20 MiB; large scientific arrays/images need a focused host
reader and a registered external-input manifest. Do not misrepresent the core as
an arbitrary microscopy image parser or universal OCR/table extractor.

Text extraction is distinct from inspecting original pages/slides/figures. Ask the
assistant to open the original when visual evidence matters. Native chart workbooks
inside PPTX are checked as inert archives, but their numeric contents still require
inspection. Improved parsers can re-extract preserved bytes without replacing the
source. Corpus progression and claim-specific approval remain separate.

## Conduct evolving experiments

Describe planned materials, lots, protocol versions, controls and independent units.
The assistant records hypotheses and competing explanations, checks missing facts,
and prepares experiment/panel contracts. Later, supply actual execution notes and
datasets. It records deviations from the plan and unresolved facts. A plan is not a
performed experiment; a computed result is not biological validation.

Ask “What controls would distinguish these explanations?” The answer should make
the distinction each control would test explicit, with cost/resource/feasibility
questions left to you. The assistant must not infer that resources or new data exist.

## Execute analyses

Say which dataset and outcome you want examined. The assistant inspects the schema,
units, missingness and hierarchy, clarifies material ambiguity, then uses or develops
versioned Python in its owning repository. Exploration stays distinguishable from a
frozen production analysis. A general script/module can receive selected copied
inputs and configuration through the runner; this is more than a fixed calculator
menu. See [execution contracts](EXECUTION.md).

Every relied-upon run records input versions and hashes, exact committed software,
checkout/patch status, repository origin and observed remote revision evidence,
environment and lock identity, parameters/seeds, plan/decisions, status/logs and
output hashes. Dirty files are recorded but are not silently executed in place of
the specified commit. The host can commit an explicitly inspected development
change before a new production run. No paid compute/API budget is assumed.

Ask to replay a run. Historical input/code snapshots are verified first. Replay
uses its recorded equality or numeric tolerances, and reports changed current
evidence separately. It does not promise identical model prose or cross-platform
numerical identity. Trusted Python is executed with operating-system rights under
the host's permission boundary; Scientist OS is not a code sandbox.

Use `analysis.register_result` to turn a selected, hash-verified supported result
JSON into a revision-linked analysis and figure for authoring. General outputs
remain recorded files until the host selects the appropriate scientific adapter.

## Review literature and synthesize studies

The host browses lawful sources and inspects original documents. A citation search
is not full-text access; inaccessible originals remain an explicit handoff. Keep
search dates/scope, publication status, exact extraction and competing evidence.

For meta-analysis, define eligibility and the estimand first. Retain all selection,
duplicate and exclusion decisions, trace effect estimates and standard errors to
exact sources, assess independence/comparability/bias, freeze the justified plan,
then synthesize and inspect influence/sensitivity/forest plots. The supplied
fixed-effect and DerSimonian–Laird methods are transparent baselines with limits,
not a universal statistical recommendation. The tools reject several declared
incompatibilities; the scientist must still assess semantic fit and undisclosed
dependence. See [controlled meta-analysis](META_REVIEW.md).

## Create and refine artifacts

Ask for a lab meeting deck, a proposal, manuscript section, figure or supplement.
The assistant drafts from current evidence, retains claim/citation/terminology/change
reports, and exposes uncertain claims. Editable PPTX and DOCX, HTML previews, SVG
and PNG figures are available. The host may use additional specialist artifact tools.

Point to a slide, panel or exact passage and request a revision. The assistant
checks the selected revision, preserves previous versions and writes an unapproved
draft. It should render the actual exported bytes and inspect pages/slides before
claiming visual review. Stale upstream evidence blocks supported authoring exports.
Historical exported files remain historical; they do not automatically disappear.

## Correct evidence and return later

Say what changed and identify its controlling source. A replacement data version
retains the old bytes and stable record history. Declared dependency links identify
affected analyses, figures and prose; undeclared dependencies cannot be discovered
mechanically. The assistant should inspect additional semantic effects and reopen
the relevant procedure. It cannot silently certify every previously written claim.

Say “pause here” or “continue the project.” Tasks, goals, decisions, open problems,
completed actions and next steps are durable records. The assistant should reload
them in later conversations. It does not need the old hidden model context. For an
interrupted external action, a missing receipt means uncertainty, not permission to
repeat it. Reconcile the actual outcome before any retry. Host transcript retention,
background scheduling and active cancellation remain host capabilities.

## Reviewer rounds and workflow improvement

Freeze exact submitted files and record snapshots, split reviewer comments into
atomic requests, consult the full inventory, and choose the least expansive adequate
response. Necessary new experiments and disputed scientific choices remain decisions
for the scientist. Reconcile clean, marked and response artifacts against the request
matrix; mechanical checks do not establish semantic response adequacy.

When a workflow fails, preserve the failure, cause and a representative successful
recheck. Update the narrowest owning procedure with its version and limits. An
unverified workaround must not become permanent policy. See the [procedure and
coverage guide](SCIENTIFIC_PROCEDURES.md).

## Evidence and limitations

[Host capability matrix](HOST_CAPABILITIES.md), [workflow coverage](WORKFLOW_COVERAGE.md)
and [prototype verification](PROTOTYPE_VERIFICATION.md) distinguish implemented,
software-tested, real-host-demonstrated and human/scientifically validated behavior.
The fictional example establishes workflow and calculation behavior only. No real
scientist adoption study, substantive systematic review, clinical utility or
biological validity is claimed.
