# From “is this biased?” to an assessment policy

**🇬🇧 English** · [🇨🇿 Česky](article-methodology.cz.md) · [News example](../examples/news/README.en.md)

The example's political articles illustrate the mechanics. The reusable part is
choosing observable questions, defining answers, and deciding what the application
does with them. The questions themselves determine the scope of the result.

## Try the complete process

```bash
./dev.sh news-lab --lang en
```

Open the printed local URL. The launcher reads your runtime key; the browser never
receives it. Editing, loading samples, validating and exporting a policy make no
model calls. **Assess both articles** makes up to two billable calls. An API error
stops the second call. Counts and available costs are shown separately per article.

1. Load the sample texts or paste your own. Changing interface language preserves
   the current articles and questions; loading sample articles replaces the texts.
2. Select the preset language (English/Czech), load it and expand its criteria.
   The Czech editor starts with Czech questions and definitions; existing runs
   retain their original language. Edit the exact instructions and the
   definitions of `present`, `absent` and `unclear`. Add or remove criteria as needed.
3. Set probability and confidence thresholds. They govern the application after
   the model answers; they are not extra instructions sent to the model.
4. Choose **Compare features only**, or explicitly select the persuasion question
   used for commentary/reporting routing. An uncertain answer or API error leads to review.
5. Validate for free. Inspect the complete questions, including the common
   framework instruction, or the full request for each article. No reference key,
   other article, filename or API key is included in those request payloads.
   API identifiers and the common library guard remain in English; your questions
   and definitions are sent unchanged.
6. Run an assessment. The report records texts, policy, exact questions, thresholds,
   fingerprint, actual model and costs. Its **Edit these texts and criteria** link
   starts a new submission; it does not rewrite the previous evidence or result.

## What did we choose in the original example?

| Criterion | What it observes | Scope |
|---|---|---|
| `welcomes_visit` | Author endorses this reception as an achievement. | Specific event; replace for another topic. |
| `rights_and_oversight` | Author advocates rights and independent scrutiny. | Political frame, not a bias verdict. |
| `people_vs_elites` | Author endorses a moral people-versus-elites contrast. | Particular rhetorical frame. |
| `leader_over_scrutiny` | Author argues for a leader's freedom from scrutiny. | Particular political argument. |
| `authorial_persuasion` | Author repeatedly evaluates or persuades in their own voice. | More broadly usable; still validate on the intended genre. |

Jev does not autonomously choose these dimensions. Both articles receive the same
questions separately. A different profile is not proof that one writer is more
truthful or that the writers disagree about the underlying facts.

## Replace a vague goal with a visible feature

“Is the author biased?” leaves the model to invent a definition. For an article
about a fictional transport proposal, a more explicit question could be:

> In `article`, does the author personally endorse the proposed free city bus service?
> Reporting a supporter’s quote without endorsement does not count.

| Answer | Definition |
|---|---|
| `present` | The author explicitly recommends or supports the proposal in their own voice. |
| `absent` | The text does not endorse it; it may oppose it, report neutrally, or only attribute support to someone else. |
| `unclear` | Mixed positioning or unclear attribution prevents a decision. |

Here, `absent` **does not mean opposition**. If support versus opposition is your
actual decision, define another question for opposition, or use an appropriate
multi-option `Rule.choose` in the library. This teaching editor intentionally uses
only present/absent/unclear feature questions.

The **general rhetoric** preset removes the visit-specific questions. It looks
for authorial persuasion, evaluative labels, disparagement of opponents and
endorsed us-versus-them rhetoric. It is an experimental starting point, not a
standard or a universally calibrated detector. It does not identify the target
of an author's support automatically, establish intent, or check factual omissions
without comparison sources. Strong opinions and factual correctness are separate.

## Take your policy into an application

Download the validated `policy.json`, put it in the target application's runtime
configuration, and use the same library interface:

```python
from sema_jev import Gate, Policy

gate = Gate(Policy.load("config/article-policy.json"))
decision = gate.check({"article": article_text})
for feature in decision.checks:
    print(feature.id, feature.status, feature.probabilities, feature.confidence)
```

The policy exports questions and thresholds. The example's optional routing rule
is application logic, separately stored as `routing_rule` in `report.json`; choose
the appropriate action in your own application. Do not interpret the aggregate
`decision.passed` as an article-quality or neutrality grade.

Start testing with a clear positive case, neutral reporting, a rejected quotation,
irony and an ambiguous case. Annotate them before looking at model output. Keep
development and evaluation cases separate and inspect confident mistakes too.
Changing question wording, language, model or thresholds requires renewed evaluation.
See [policy methodology](methodology.en.md) and [credentials](credentials.en.md).
