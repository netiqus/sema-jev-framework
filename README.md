# Sema Jev Framework

**Semantic decision gates for Python.**

[![CI](https://github.com/netiqus/sema-jev-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/netiqus/sema-jev-framework/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Alpha](https://img.shields.io/badge/status-experimental_alpha-orange)](docs/limitations.en.md)

**🇬🇧 English** · [🇨🇿 Česky](README.cz.md)

Sema Jev is a small, independent Python library for adding semantic decision
gates to existing applications. [Jev from TypeSafe](https://typesafe.ai/) assesses
the supplied evidence; Sema Jev validates the response, applies versioned policies
and returns an explicit `pass`, `fail` or `review` result with token and cost
accounting. Your application controls the next action.

```python
from sema_jev import Gate, Status

gate = Gate("Does `message` explicitly request a refund?")
result = gate.check({"message": "Please refund the duplicate payment."})

if result.status == Status.PASS:
    print("Send to the refund queue")
elif result.status == Status.FAIL:
    print("Keep in general support")
else:
    print("Request more evidence or a human review")
```

**0.2.0a3 · experimental alpha · Python 3.11+ · no runtime dependencies**

A [netiqus](https://github.com/netiqus) project, licensed under MIT.
Independent of TypeSafe AI; not affiliated with or endorsed by the makers of Jev.
Verified on Linux with Python 3.11–3.14. Windows remains unverified.

[Quick start](#quick-start) · [Article lab](#try-the-article-lab) · [API](docs/api.en.md) · [Agent integration](docs/agent-integration.en.md) · [Limitations](docs/limitations.en.md)

## Why this project

Sema Jev grew out of practical experiments at netiqus. It shares one approach
to making semantic decisions easy to try, inspect and reuse in everyday Python
applications. The library, examples and guides are here to offer ideas you can
adapt to your own work. Helping someone understand the possibilities or solve
a practical problem is the purpose of this project.

## Where it fits

| Application needs to… | Ask the model to assess… | Keep in your application… |
|---|---|---|
| Route a message | Whether the sender actually requests a refund | Account permissions and payment execution |
| Compare articles | Whether the author endorses a claim or merely quotes it | The feature definitions and resulting queues |
| Check a generated draft | Whether it addresses the requested change | Compiler, tests and approval rules |
| Repair incomplete output | Which declared requirements are unmet | A bounded revision callback |

Use ordinary Python checks for exact facts. Use a semantic gate for a judgement
about supplied text or evidence. A successful check is evidence for your workflow,
not proof that an action is correct or authorised.

Sema Jev focuses on standalone Python integration: explicit outcomes, versioned
policies, fixed checks and per-request accounting. The
[methodology guide](docs/methodology.en.md#related-approaches) places it alongside
existing semantic operators and native integrations in larger frameworks.

## Quick start

The package is **not yet on PyPI**. Install from a checkout or a built wheel.
Download a built wheel from [GitHub Releases](https://github.com/netiqus/sema-jev-framework/releases).

```bash
git clone https://github.com/netiqus/sema-jev-framework.git
cd sema-jev-framework
python3 -m venv ../sema-jev-env
source ../sema-jev-env/bin/activate
python -m pip install .
```

These commands use a Linux shell and keep the virtual environment outside the
checkout. In an existing application, install into that application's environment.
A wheel can be installed with `python -m pip install /path/to/package.whl`.

For a first live request, save the opening Python example as `first_gate.py`
alongside the checkout directory (`../first_gate.py`). Supply `OPENROUTER_API_KEY` through your application's
secret manager or environment. For an interactive test, this hidden prompt avoids
putting the key in shell history:

```bash
python - <<'PYCODE'
import os
import runpy
from getpass import getpass

os.environ["OPENROUTER_API_KEY"] = getpass("OpenRouter API key: ")
runpy.run_path("../first_gate.py", run_name="__main__")
PYCODE
```

The example sends one **billable** assessment to OpenRouter/Jev. Pricing lookup
is separate; importing the package makes no request. No automatic retries occur.
The library does not discover `.env` files or store credentials.
See [API keys](docs/credentials.en.md) for explicit provider keys and other setups.

Prefer to start without a key? The [offline example](examples/offline.py) uses
clearly labelled fixtures:

```bash
python examples/offline.py
```

It tests the integration flow, not the model's ability to understand text.

## Three outcomes, explicit handling

| Result | Meaning | Typical next step |
|---|---|---|
| `pass` | Every required check passed the configured rules | Continue the workflow |
| `fail` | At least one check established that a requirement was unmet | Route elsewhere or revise |
| `review` | No check established failure, but evidence, confidence or the service was insufficient | Collect evidence or review |

A definite failure takes precedence over another check's uncertainty. Inspect
`result.checks` when you need each feature separately. `result.error` distinguishes
provider errors. `if result:` raises an error on purpose; use `.passed` or `.status`.

Defaults of `0.85` answer support and `0.60` confidence are starting settings,
**not measured accuracy**. A model can be confidently wrong. Your questions,
examples and validation data determine whether a gate is useful in your domain.

## Try the article lab

Two longer fictional articles describe the same diplomatic visit with different
editorial framing. The lab exposes the exact questions and answer definitions,
so you can see what the experiment actually measures.

- English articles, criteria and interface by default; Czech counterparts included.
- Edit both texts, add criteria, adjust thresholds and inspect the complete request.
- Preview without an API call, then explicitly run up to two paid assessments.
- Compare individual features, uncertainty, input/output tokens and costs.
- Export a versioned policy and reuse it with `Gate(Policy.load(path))`.

With Python and [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:

```bash
./dev.sh news-lab             # opens a local server; no model call on startup
./dev.sh news --lang en       # generate an HTML preview without the API
./dev.sh news-lab --lang cz   # Czech interface, articles and default criteria
```

Open `http://127.0.0.1:8770/` for the editor. The launcher prints its separate
runtime directory; optional keys belong in that directory's `config/runtime.env`.
See the [article guide](examples/news/README.en.md) and
[how to choose criteria](docs/article-methodology.en.md).
The example measures declared textual features, not which political opinion is right.

## Grow from one condition

The same interface supports versioned JSON policies, several criteria, fixed
checks from real tools, async calls, a bounded repair loop and a JSON CLI.

```python
from sema_jev import Gate, Policy

gate = Gate(Policy.load("policy.json"))
result = gate.check({"article": article_text})
print(result.cost.input_tokens, result.cost.output_tokens)
print(result.cost.billed_usd)  # None means unknown, not free.
```

See [integration recipes](examples/integrations.py), the [API guide](docs/api.en.md)
and the [copyable agent brief](docs/agent-integration.en.md).
Installing the package registers `sema-jev` in the active environment; no system
PATH modification is needed. `python -m sema_jev.cli` works with the same arguments.

## Verification and development

```bash
./dev.sh check    # lint, docs, types, offline tests, build and clean wheel install
./dev.sh demo     # explicitly simulated answers; no key required
```

Source and runtime are kept separate. For a checkout under `~/dev`, generated
files go under the same relative path in `~/dev-out`; elsewhere a sibling
`<checkout>-out` directory is used. Override with `SEMA_OUT_DIR` if needed.

CI tests the library contract without real keys. Live checks through OpenRouter
have also been performed; the direct TypeSafe adapter has offline contract tests
but has not been verified live. Synthetic examples are not an independent benchmark.
See [verification limits](docs/limitations.en.md) and the [evaluation guide](evals/README.en.md).

## Documentation

| Start here | Then explore |
|---|---|
| [API and CLI](docs/api.en.md) | [Architecture](docs/architecture.en.md) |
| [API keys](docs/credentials.en.md) | [Operations and releases](docs/operations.en.md) |
| [Policy methodology](docs/methodology.en.md) | [Article methodology](docs/article-methodology.en.md) |
| [Agent integration](docs/agent-integration.en.md) | [Contributing](CONTRIBUTING.en.md) |
| [Limitations](docs/limitations.en.md) | [Changelog](CHANGELOG.en.md) |

English is the primary language of the public project, code and comments.
Czech guides are available through the language links. Public examples contain
fictional data only. The [MIT licence](LICENSE) covers the code; model access
requires your own provider account.

## Help shape what comes next

If this project sparks an idea or helps with your work, you're welcome to help
improve it. Share a use case, report an unexpected result, improve an example
or contribute code — small contributions count too.

[Open an issue](https://github.com/netiqus/sema-jev-framework/issues)
or see the [contribution guide](CONTRIBUTING.en.md) to get started.
