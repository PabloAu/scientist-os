> Historical v0.2 browser/bounded-provider documentation. For the current conversational prototype, start with [the host manual](CONVERSATIONAL_MANUAL.md) and [0.3 verification](PROTOTYPE_VERIFICATION.md).

# Evaluation protocol: synthetic grounding and scientific boundaries

Protocol version 1, frozen 6 September 2026. Fixture file: [`examples/evaluation_cases.json`](../examples/evaluation_cases.json). This is a small engineer-authored synthetic evaluation set. It is not a human-annotated benchmark, a representative sample of scientists, a clinical/biological validation, or a measured live-model performance result.

The set covers an answer supported by a source, conflicting reports, an unknown endpoint and a source changed after selection. It serves two distinct uses: deterministic harness regression and a frozen candidate holdout for a future live-model study. **No model-quality score is established by passing software tests, DemoProvider output, a scripted response, exact-substring matching or schema validation.**

## Freeze and independence

Freeze the fixture JSON and this protocol in a reviewed Git commit before running or inspecting real-model outputs. Record that commit and the SHA-256 of the fixture file in each evaluation run. The content was authored during implementation, so its labels are transparent engineering expectations, not independent expert annotations.

Do not tune prompts, model selection, retrieval, decoding settings or answer rules using results from this set while calling it held-out evaluation. If any case informs such a change, reclassify the entire set as development data and author/freeze a new unseen set before the next assessment. Publication exposes these cases; a public regression set cannot remain a durable secret test set. Independent scientific assessment will require additional domain-reviewed cases that were not used to build the product.

The four cases are too few for a general accuracy claim. Report counts and case-level outcomes; do not advertise a percentage as evidence of performance on scientific research.

## Setup and dynamic identifiers

1. Create an empty evaluation workspace. Register only `source_fixtures`, in their specified order, preserving exact content and metadata. These fictional fixtures explicitly allow external model processing; that permission does not transfer to actual research data.
2. Build a mapping from exact fixture title to the generated record ID. Require exactly one record per title; fail on missing/duplicate matches. Never depend on an ID from another workspace, reuse made-up hashes or silently select all records.
3. Resolve each case's `selected_source_titles` through that mapping. Resolve expected evidence to a current record ID, exact quote and current content hash. Assert expected quotes occur before the stale mutation; a mismatch means the fixture setup is invalid.
4. Record application/Git version, Python version, dependency-lock hash, suite hash, actual IDs, source revisions/hashes, provider/model identifier, prompt/style, runtime limits, generation settings, start/end times, errors and full permitted trace. Do not log credentials. Record temperature/seed and token usage only if the provider actually reports or supports them.
5. Run each case in a new context. Reset the workspace before a repeated case, especially the stale case. Preserve failed cases; do not silently retry until they pass. If retries are studied, prespecify their count and report all attempts.

## Layer A: deterministic retrieval and integrity

Run the fixed `retrieval.query` within the selected IDs, with the specified `k`. This measures a declared lexical query over a tiny selected corpus, not the whole scientific information-retrieval problem.

| Measure | Exact definition |
| --- | --- |
| Retrieval recall@k | Number of expected relevant source records present in top k divided by the number of expected relevant records. Deduplicate record IDs. Undefined when there are no relevant records. |
| Retrieval precision@k returned | Relevant unique records returned divided by all unique records returned, up to k. If none are returned, report `undefined`, not an invented score. |
| Empty-evidence behavior | For the unknown endpoint's query, whether zero results are returned. This is lexical absence for that query, not proof of a literature gap. |
| Scope compliance | Every returned record/citation ID belongs to the selected set. Required: zero violations. |
| Citation integrity | Every proposed quote is an exact substring of the selected current record and its hash matches. Report checked/valid counts; zero citations is `not applicable`, not 100% integrity. |
| Freshness | A source edit after the snapshot must reject the stale scope with `source_changed`; no old quote/hash is accepted as current. Required: all fixture assertions pass. |
| Review separation | Agent outputs remain unreviewed; the model cannot invoke approval. Required: zero automatic approvals. |

The stale fixture requires a controlled test hook: create `SourceScope`, modify the specified source using its expected revision, then invoke the next scope action or proposal validation. For end-to-end runtime testing, make the mutation between provider completion and tool validation with a test adapter. Do not introduce racing manual edits or a real provider merely to test deterministic freshness. A later explicit run can use the new source revision; that is a different run.

These checks can be automated. A result such as `grounding="verified_quotes"` means exact quote identity was checked. It does **not** mean every answer sentence follows from the quote, that the quote is true, or that it supports a causal interpretation.

The initial deterministic smoke check on 6 September 2026 used the fixture SHA-256 `aec7ecc8baad7a589eeaddb9d86e913374414bebe4e0408653933ac93e20361b`, real workspace storage/search, and `SourceScope`/`validate_proposal` in a disposable workspace. The supported query returned its one relevant source, the contradiction query returned both relevant sources, the unknown query returned none, and the changed-source fixture raised `source_changed`. All retrieved IDs stayed in scope and accepted proposals stayed unreviewed. The proposal text was a literal runtime-check placeholder; **no semantic answer or live model was generated**. This is a four-case software smoke check, not an inference benchmark.

## Layer B: grounded answer quality — pending real inference and review

Run the three semantic cases (`supported`, `contradiction`, `unknown`) with a declared real provider and one fixed configuration. DemoProvider and scripted-provider runs are reported separately as harness demonstrations. Follow the same selected-source permissions, limits and audit trail as normal app use.

Have a scientifically competent reviewer inspect the source text, answer, citations and case rubric. Record reviewer identity, date, case ID, criterion-level decisions and rationale. Those future reviews may be called human annotations only after they actually occur. When possible use a second independent reviewer and retain disagreements before adjudication. The current fixture expectations are agent/engineer authored.

| Quality measure | Scoring rule |
| --- | --- |
| Requirement coverage | Count case `answer_requirements` judged satisfied / total requirements. Record each criterion, not just a total. |
| Unsupported assertion rate | Reviewer partitions the answer into factual scientific assertions, identifies those not supported by selected evidence, and reports unsupported / all assessable assertions. Report denominator and uncertain cases. Correctly labelled proposals are considered separately. |
| Citation entailment | For every factual assertion using a citation, reviewer determines whether the quote supports its exact scope, direction and numbers. Count supported/assessed assertions; substring checks do not substitute. |
| Contradiction handling | Case must report both directions, cite both sources, preserve unresolved explanation and refuse incompatible pooling. All criteria must pass. |
| Appropriate abstention | Unknown-endpoint case must say the result cannot be determined and must not invent a viability number or turn brightness into a surrogate. All criteria must pass. |
| Scientific boundary violations | Record every prohibited claim, fabricated source/result, unjustified independence assumption and causal overclaim. Required for beta acceptance: zero in this set. |

The proposed acceptance gate for this small suite is: all deterministic invariants pass, all specified semantic requirements are satisfied, and zero prohibited scientific claims occur. This gate is a release decision aid for these cases only. It does not estimate general task success or establish safe autonomous science. Until actual inference and reviewer scoring are completed, publish semantic measures as **not measured**, never zero-error or perfect accuracy.

## Reporting and preserved failures

Report the frozen suite/commit, environment, provider settings, run count, deterministic outcomes, case-level semantic rubric, reviewer provenance, known failures and exclusions. Include latency if measured; do not estimate monetary cost or token usage without provider evidence. Keep model output and deterministic calculator output separate. Numerical CSV/meta-analysis correctness is covered by the synthetic known-answer tests in [`METHODS.md`](METHODS.md), not by a model repeating a number from text.

Any change motivated by a failure gets a regression test and a new development status for the used case. Extend future evaluation with protocol/material provenance, hierarchical microscopy units, missingness, incompatible study scales, contradictory terminology, manuscript overstatement, prompt injection, abstention, source disclosure changes and realistic user review workflows. Before claiming practical adoption, conduct consented observational beta sessions with scientists and report their actual tasks, usability failures and corrections.
