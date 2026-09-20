# 📰 One visit, two different stories

**🇬🇧 English** · [🇨🇿 Česky](README.cz.md) · [← Project](../../README.en.md)

This example uses Sema Jev to recognise how an author writes about an event.
Readers can choose whichever argument they find persuasive. The application
tracks observable features and can route a text to a commentary or review queue.

## Articles to read

| Article | English | Czech |
|---|---|---|
| A | [article_a.en.txt](article_a.en.txt) | [article_a.cz.txt](article_a.cz.txt) |
| B | [article_b.en.txt](article_b.en.txt) | [article_b.cz.txt](article_b.cz.txt) |

All people, countries, media outlets and events are fictional. In both accounts,
Prime Minister Mara Vesk receives President Oren Valek at Eastmere. The meeting
lasts 110 minutes; a hotline and technical talks are planned, and a grain corridor
will be considered. No ceasefire or energy contract is agreed. Figures for detained
journalists, protesters and rising energy bills also match. The emphasis,
interpretation and the author's own evaluations differ.

Both are extended **opinion pieces**, both make an argument, and both acknowledge
inconvenient facts. This is not a contest to select the correct political opinion.
The Czech counterparts preserve the factual basis and rhetorical devices; they
are not independently validated benchmark translations.

## See and edit the assessment method

The [practical methodology guide](../../docs/article-methodology.en.md) explains
why each criterion was chosen, what transfers to other genres, and how to turn
an imprecise bias question into an observable feature.

```bash
./dev.sh news-lab --lang en  # local editor; opening it makes no paid call
```

The editor lets you replace both articles, add/remove questions, define all three
answers, adjust thresholds, inspect the full requests for free, and run up to two
paid assessments. The original visit preset and an experimental general rhetoric
preset are available. Export a policy for `Gate(Policy.load(...))`; import it again
by pasting its JSON. Each result retains the exact policy and request questions.
Routing is a separate application choice. Recent completed runs link back to their
saved results and can be reopened for editing.

The Czech editor starts with Czech questions and answer definitions. Both presets
have `.en.json` and `.cz.json` variants; Czech versions use `1-cz`. To load another
variant, select **Question language for the preset to load**, then click a preset.
Switching the interface or loading articles does not translate edited questions.
Historical reports retain their actual wording; translating criteria requires
a new assessment.

## Run it

From the repository root:

```bash
./dev.sh news --lang en       # English article preview, no API request
./dev.sh news --lang cz       # Czech article preview, no API request
./dev.sh news-live --lang en  # at most two billable requests; requires a key
./dev.sh news-live --lang cz  # assess the Czech texts directly
```

The key belongs only in the environment or runtime `config/runtime.env`; see
[operations](../../docs/operations.en.md). The launcher runs everything in `dev-out`.
Outputs go to `artifacts/news-en-preview/` or `news-en-live/` (`news-cz-…` for Czech).
Open `index.html` for the default English interface, or `report.cz.html` for Czech. Each report has an interface-language
switch, complete articles, a legend and a separately collapsible author's reference key.
The HTML switch does not translate evidence or questions. `--lang` selects both articles and the default preset in that language. The direct CLI `examples/news_compare.py --policy PATH` can select a different policy.

Preview mode invents no model answers: it shows **Not measured**, zero assessment
attempts and no probability figures. Live mode also saves `report.json`, answer
distributions, confidence, policy/model identity, input/output tokens, a calculation
using available OR prices and any amount returned by the API. Unknown amounts are
not counted as zero. A provider error on the first article stops the second request.

## A short plain-language legend

| Question | What it looks for |
|---|---|
| Welcomes the visit | The author personally presents the reception and meeting as a political achievement. |
| Rights and oversight | The author advocates rights and independent scrutiny as constraints on politicians. |
| People versus elites | The author pits authentic ordinary people against a detached or self-serving elite. |
| Leader over scrutiny | The author wants greater freedom for the leader and frames scrutiny as an obstacle. |
| Authorial persuasion | The author repeatedly evaluates, recommends or uses irony. |

**Present** means a feature was recognised, **Absent** means it was absent from
the author's own argument, and **Review** means uncertainty or an error. These are
descriptions, not quality grades. Each question has its own result. The aggregate
`Decision` object's `pass/fail` is not used as a verdict on an article: a mixed
feature profile is normal here.

The default policy requires an option probability ≥ 0.85 and confidence ≥ 0.60.
Confidence is not measured accuracy on articles. These initial settings are not
calibrated. All five questions are sent together, separately for each article.
The original language experiment used identical English questions for EN and CZ,
changing only the input text. The new Czech preset also translates the questions,
so differences cannot be attributed solely to article language. The original
`policy.json` remains an English alias of `policy.en.json`. Jev does not provide prose explanations; the reference
excerpts below were written by us.

## Practical application output

Confidently detected authorial persuasion routes to `commentary_queue`; its
confident absence routes to `reporting_queue`. Any uncertain feature or error
routes to `review_queue`. This conservative application rule is visible in
the `route` function in the [example](../news_compare.py). Other applications
can select individual features without assigning a political identity to the author.

<details>
<summary>Author's reference key — try your own assessment first</summary>

A intentionally uses a liberal-institutional frame; B a populist frame.
These frames are not generally mutually exclusive, and our five features do not
provide a universal definition of either.

| Feature | A | B |
|---|---|---|
| Welcomes the visit | absent | present |
| Rights and oversight | present | absent |
| People versus elites | absent | present |
| Leader over scrutiny | absent | present |
| Authorial persuasion | present | present |

Both quote Pell's same slogan. A rejects it; B endorses it. Detecting the words
"ordinary people" is therefore insufficient. B also mentions parliament and
journalists; these words alone do not establish advocacy of independent scrutiny.

[reference.json](reference.json) contains expectations and exact excerpts. These
are author annotations, not measured Jev answers. They never reach the model.
An illustrative excerpt cannot alone establish that a feature is absent from
the entire article.

</details>

## Your own texts and control cases

After `./dev.sh sync`, use the runtime and its Python:

```bash
cd ~/dev-out/sema-jev-framework
.venv/bin/python examples/news_compare.py --article-a /path/a.txt --article-b /path/b.txt
.venv/bin/python examples/news_compare.py --article-b examples/news/article_a.en.txt
```

The first command previews custom texts; the second creates an A/A control pair.
Add `--live` for paid evaluation. When running directly, the key must already be
in the environment: only the launcher loads `config/runtime.env`. `--output`
selects another destination outside `dev`. Custom inputs hide the bundled reference key.

Further controls include swapping A/B to B/A, replacing a quote with the author's
endorsement, or changing language. Texts are assessed independently; filenames
and expected answers are excluded from requests. A/A or CZ/EN agreement is not
enforced by code: disagreement is an observation to investigate. This pair is a
teaching aid, not evidence of accuracy, covert coordination, factual truth or
the intentions of real people.

## A side observation: translation as another framing layer

This example was created to explain the integration and compare writing styles. Independently assessing its English and Czech texts suggested another possible use: comparing an original with a free translation for shifts in emphasis, evaluation or whose opinion is being expressed.

In the first independent EN/CZ run on 19 September 2026, model
`typesafe/jev-1.13-20260917` received the same five English questions for each
article. All ten feature decisions matched across languages and agreed with the
author's reference key. The numbers were not identical: for welcoming the visit
in article B, support for "present" was 99% in EN and 92% in CZ; confidence was
99% and 88%, respectively. This run did not establish a translation-induced
change in framing.

A difference can point to passages worth checking. It does not by itself show that a translation changed the framing: language sensitivity and variation between model runs can also affect the scores. This is a follow-up idea from the teaching experiment, not a validated translation check.
