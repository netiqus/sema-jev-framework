# Designing and evaluating policies

**🇬🇧 English** · [🇨🇿 Česky](methodology.cz.md)
## Implemented mechanisms and proposed methodology

The library provides policy execution mechanics. Included questions are
**illustrative experimental examples**, not a validated universal methodology.
Default thresholds are not accuracy certificates. Testing infrastructure and
evaluating model judgement are separate activities.

## From a goal to questions

1. State the application's decision and the consequences of false approvals and rejections.
2. Find an established domain methodology; record its source, version and scope.
3. Translate each applicable criterion into one observable question identifying
   the evidence fields. Preserve the original meaning without silently adding assumptions.
4. Evaluate counts, dates, permissions and tool results deterministically.
5. Describe satisfied, unsatisfied and insufficient-evidence cases.
6. Freeze wording and thresholds for a policy version and evaluate an independent set.
7. Re-evaluate changes to the model, wording or thresholds; use the content fingerprint.

Potential sources include a project's review checklist, an applicable standard
or a research dataset's annotation manual. Knowing a methodology's name does
not establish a faithful implementation. This alpha claims no such standard.

## Practical controls

- Invoice topic and urgency are separate questions. Define urgency explicitly;
  high topic confidence cannot establish it.
- A binary yes probability is not a score question's confidence.
- Changing a threshold does not fix a poorly chosen question. Show review reasons.
- Distinguish the author's position from an attributed quote in the instructions.
- Article tests need A/B, B/A, A/A, paraphrases, negation, quote changes and languages.
- Ground conclusions in specific inputs, outputs and request identities. One
  successful case is neither a benchmark nor evidence of universal reliability.

## Measuring quality

Keep development and evaluation sets separate. Once you have seen a failure and
adapted a question, that example no longer provides independent evaluation.
Inspect a random sample of high-confidence results as well.

TypeSafe derives `confidence` from the shape of the answer distribution. It is
not an independent verification or a measured probability of correctness. Keep
option support, confidence and observed correctness separate. A threshold of
`0.9` does not establish 90% accuracy, and thresholds do not automatically
transfer between question types, languages, models or provider implementations.

Tune on development data, then report errors among automatically accepted
cases alongside coverage on untouched evaluation data. Repeat a subset of
identical requests and test meaning-preserving changes to wording and evidence
order; do not assume stable decisions merely because the facts are unchanged.

Report sample count, automatic-decision coverage, false passes, false rejections,
reviews and API errors. Report known cost subtotals and the number of requests
with unknown costs. Percentages on a tiny set are not production-quality estimates.

`evals/` provides a small synthetic set and runner. It is a process smoke test;
independent real examples are required before production use. The
[article example](../examples/news/README.en.md) illustrates feature design and
quotation attribution; its author's reference key is not an independent benchmark.

## Related approaches

Semantic conditions build on established work.
[LOTUS](https://github.com/lotus-data/lotus) offers semantic operators for bulk data
processing. [LangChain](https://www.langchain.com/blog/building-a-harness-with-jev)
provides a native TypeSafe integration and experimental agent middleware.
Applications already using such frameworks should evaluate their native options.
Sema Jev focuses on a small standalone gating API for existing Python code.

[jev-align](https://github.com/sutro-sh/jev-align) explores human feedback and
GEPA-based definition refinement. Sema Jev currently executes supplied policies;
it does not train models, fit calibration parameters or automatically optimise
questions. Its synthetic evaluation runner checks the process, not domain accuracy.

## Primary sources

- [Primitives](https://docs.typesafe.ai/primitives): questions, independent answers and composition.
- [Confidence](https://docs.typesafe.ai/confidence): probability versus confidence.
- [Jev 1.13 known limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13).
- [API](https://docs.typesafe.ai/api).

- [Representation robustness study](https://research.prose.md/articles/representation-robustness/):
  reported sensitivity to evidence arrangement in controlled graph tasks; not a
  benchmark of this library or its article example.

Checked against documentation available on 20 September 2026; APIs and models may change.

A [worked article-policy guide and editor](article-methodology.en.md) connects this
process to editable questions, complete request inspection and policy export.
