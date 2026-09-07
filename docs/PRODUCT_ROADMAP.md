> Historical v0.2 browser/bounded-provider documentation. For the current conversational prototype, start with [the host manual](CONVERSATIONAL_MANUAL.md) and [0.3 verification](PROTOTYPE_VERIFICATION.md).

# Product roadmap and evidence gates

Version 0.2 implements the authoring studio, original PDF/Office text import, explicit excerpts and Crossref bibliographic discovery. Those portions of sections 3 and 5 below are delivered; OCR, table reconstruction, systematic search histories and official journal connectors remain open. The [authoring guide](AUTHORING_GUIDE.md) defines current behavior.

Scientist OS is intended first for individual experimental scientists, especially biology and microscopy researchers who need a traceable path from evidence and methods to an analysis, figure and manuscript. The next priorities should be driven by observed work and failures. This roadmap sets an order and completion gates; it promises no dates, paid resources, adoption numbers or unsupported capabilities.

The current beta provides local records/provenance, deterministic CSV/meta-analysis tools, bounded model adapters, a selected-record MCP bridge, human review, lifecycle checkpoints and portable exports. Its software checks use synthetic fixtures. Real-model answer quality, independent scientific validation and sustained use by scientists remain separate work to measure.

## 1. Pilot the complete workflow with individual scientists

**User problem:** a research assistant is useful only if a scientist can bring real work into it, understand its decisions and return later without losing context.

Run consented, observed sessions around a small authentic question. Begin with data whose owner has described the experiment, meaning, limitations and permitted use. Choose a bounded case with a source, protocol, material, dataset, analysis, figure and short writing output. Keep private research local unless the owner explicitly permits the selected model disclosure.

Observe onboarding, source registration, hierarchy/independence choices, record linking, error recovery, the review→regenerate workflow and backup/reopening. Record where the scientist needs assistance, where the interface misleads them and which metadata is too burdensome or missing. Preserve negative feedback and cases where the product is not suitable.

**Gate:** publish an appropriately de-identified pilot report with actual participant consent, tasks attempted/completed, observed problems, corrections and unmeasured areas. Do not describe developer walkthroughs as scientist adoption. Prioritize fixes that block a complete workflow before adding more agents or formats.

## 2. Evaluate real models and provider interoperability

**User problem:** connection compatibility, exact citation checks and useful scientific reasoning are different properties.

Exercise a small set of explicitly chosen local/remote providers with documented models, transport settings and resource authorization. Check tool calling, failure handling, source selection, source changes and permission revocation. Then evaluate grounded answers, contradiction handling, appropriate abstention and scientific overstatement against a frozen protocol. Use [EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md); any public case used to tune the system becomes development data.

Add domain-reviewed cases that were not used for implementation. Have named scientific reviewers assess criterion-level evidence support and record disagreements. Separate model hallucination from missing source information and from an inappropriate experimental design. Measure latency/cost only from actual observations; establish a budget before any paid run.

**Gate:** release a provider compatibility matrix and case-level evaluation record with model/version/configuration, source/fixture hashes, reviewer provenance, failures and limitations. Report software invariants separately from semantic quality. Do not generalize a few synthetic cases into an accuracy claim for scientific research.

## 3. Add governed PDF and table ingestion

**User problem:** scientists should not need to manually prepare every excerpt, but extraction must not promote OCR or table parsing into verified evidence.

Build an import pipeline that preserves the original bytes and records original-file identity, acquisition source, rights, publication status and page/region locators. Detect native-text versus scanned/mixed documents, show extraction warnings and make the original passage/table visible during review. Distinguish registration, machine extraction, mapping, exact-original verification and permitted scientific use.

Treat document text, links and embedded instructions as untrusted data. Preserve contradictory passages and table headers/units. Keep raw images/PDFs in appropriate storage and avoid automatic third-party uploads. A discovered abstract or metadata page should remain discovery information until the needed primary evidence is available.

**Gate:** demonstrate exact-original checks on licensed/synthetic fixtures, numerical table reconstruction with denominators/units, OCR failure cases, unchanged input hashes and reviewer correction. A failed extraction must remain a visible failure; no silently generated values or automatic source approval.

## 4. Add domain analysis adapters with reproducible execution

**User problem:** microscopy and other experimental domains need more than grouped CSV means, while arbitrary model-written code is difficult to audit and reproduce.

Define narrow adapters for selected scientific pipelines in their owning repositories. Start with a user-validated file schema and a known scientific question. Bind each run to independent units and hierarchy, an estimand, hypotheses/metrics where applicable, exact input manifests, code commit, environment lock, configuration, seeds, exclusion/QC decisions and output hashes.

Add approved execution as a separate capability with explicit resource limits and a reviewed isolation design. Keep source files immutable and outputs in designated locations. Preserve classical/physical baselines, failures, negative comparisons and downstream scientific bias checks. Do not reuse an existing project's held-out scientific test data as development material for a new model.

Possible methods include hierarchical/paired designs, longitudinal measurements and domain-specific figures. Select these from pilot needs rather than adding a catalogue of methods without ownership or validation.

**Gate:** a domain owner can replay the complete analysis from declared inputs; known-answer and failure fixtures pass; representative data limitations are recorded; outputs link to exact code/data without suggesting that execution itself established biological validity. Human approval remains separate from method execution.

## 5. Add literature and journal connectors

**User problem:** literature discovery and journal requirements change, and source selection should be documented rather than hidden in a model's memory.

Integrate selected authoritative discovery services and official journal sources through explicit read-only connectors. Preserve query, date, filters, bibliographic identity, acquisition status, inclusion/exclusion rationale and contradictory/negative results. Search should support evidence sufficiency rather than only confirming a proposed narrative. Respect access controls and source-specific usage rights.

For journals, record the exact official scope, article type, submission requirements and any applicable fees with retrieval dates. Keep comparisons tied to those records and the user's intended audience. An agent recommendation is not an acceptance prediction or a verified current fact when its source has expired.

**Gate:** a reviewer can reconstruct the search and explain every included/excluded source or journal criterion; stale/contradictory metadata is visible; restricted full text is not acquired or disclosed without authority. No automatic submission or publication is introduced by adding discovery.

## 6. Decide on shared-lab hosting and signed installation

**User problem:** some scientists will need simpler installation or collaboration across a lab, but those require different operational commitments from a local beta.

Evaluate these as separate decisions after pilots identify demand:

- **Signed desktop installer:** wrap the same Python core; verify packaged dependencies/notices, operating-system support, code signing, updates, rollback and workspace preservation. Avoid a second scientific implementation with diverging behaviour.
- **Shared-lab or hosted deployment:** design authenticated identities, roles, tenant/workspace isolation, secret handling, source disclosure, retention, backups/recovery, quotas, audit anchoring and operational monitoring. Revisit consent and institutional requirements using actual deployment facts.

Do not expose the current loopback service to the internet as a shortcut to collaboration. A hosted model endpoint does not make the workspace a hosted application, and a typed reviewer name is not a digital signature.

**Gate:** demonstrate migration/recovery, authorization boundaries and operational ownership for the chosen distribution. Inspect the exact installer/service release and its dependency licenses. Describe supported operating systems and hosting guarantees only after testing them.

## Cross-cutting product requirements

At every step, keep the human's ability to correct a question, selection, interpretation and style. Preserve explicit supported/proposed/unknown states and record why a scientific decision changed. New tools must have typed inputs, declared effects, bounded execution, observable failures and human review suited to their authority.

Keep the provider interface separate from scientific tools so changing a model does not rewrite the research record system. Keep database schema changes behind reviewed migrations, backups and previous-version fixtures. Preserve original licensing and source-specific confidentiality. Design useful defaults, then expose targeted customization informed by real users rather than unrestricted configuration that hides assumptions.

Track practical outcomes before growth claims: successful recovery after a source change, a reproducible figure, understandable exclusions, a correctly scoped paragraph and the scientist's ability to identify what remains uncertain. Record measured usability and scientific quality separately from implementation volume or test counts.

## Contribution and evidence record

| Contributor or evidence class | What is established | What must not be inferred |
| --- | --- | --- |
| Pablo's product/scientific direction | Selected Scientist OS as the first project; supplied the source workflow and desired end-to-end capabilities; prioritized individual experimental scientists/biology/microscopy; required human direction; authorized a separate repository and Apache-2.0 for generic product work | That he personally wrote every new implementation line, performed every automated test, or independently validated all generated scientific methods |
| Agent-assisted engineering | Implemented the new generic software, authored documentation and synthetic fixtures, inspected the source and executed reported software checks under the user's direction | Human annotation, independent biological validation, original experimental measurements or proof of practical adoption |
| Existing private research workflow | A source of provenance, lifecycle and evidence-control requirements, with its specific records retained separately | Public permission for its research payloads, full feature parity, or scientific conclusions validated by the new beta |
| Future pilot scientists/reviewers | No pilot contribution or independent annotation is claimed before consented participation and recorded review occur | Users, endorsements or successful outcomes that have not happened |

For future work, record the user's scientific decisions and hands-on experiments, coding, analyses and reviews as they occur, separately from generated implementation. Maintain commit/run/decision references for material claims. The portfolio should make it possible to explain both the software and the scientific judgement behind its use without conflating their authorship or evidence.
