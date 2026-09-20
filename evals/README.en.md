# Evaluating a policy

**🇬🇧 English** · [🇨🇿 Česky](README.cz.md) · [Project](../README.md)

`cases.json` contains 12 authored examples covering negation, attributed quotes,
conditions, missing context, instructions embedded in evidence and Czech/English
inputs. The expected labels were written by the example author; they are not an
independently validated benchmark. Czech strings in this mixed-language dataset
are deliberate test evidence, not the application's default language.

`./dev.sh evaluate` explicitly starts **billable** OpenRouter assessments.
Put the key in the runtime configuration. Results go to
`artifacts/evaluation.json` in the runtime; the series stops on the first operational
error. The report includes decision coverage, a confusion table, false-pass and
false-fail counts, and known/unknown costs.

Use this set to catch basic problems, not to derive production thresholds.
Before deploying a policy, obtain representative data, independent labels,
separate tuning and final test sets, and model-change checks. Store real inputs
outside the source tree. Rewording a question requires a new evaluation; policy
version and hash identify the assessed rules.

[Methodology](../docs/methodology.en.md) · [Limitations](../docs/limitations.en.md)
