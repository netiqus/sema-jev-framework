# Contributing

**🇬🇧 English** · [🇨🇿 Česky](CONTRIBUTING.cz.md) · [Project](README.md)

Start with an issue describing the observable problem or integration need.
Keep changes focused. The project is maintained under the **netiqus** GitHub
organisation and uses the [MIT licence](LICENSE).

## Local checks

Install Python 3.11+ and uv, then run `./dev.sh check`. The launcher keeps the
virtual environment, caches, build output and reports outside the checkout.
Normal tests are offline; no provider key is required. `./dev.sh demo` runs the
fixture-based example. See [operations](docs/operations.en.md) for output paths.

Code, identifiers, comments, errors and default UI text are English. Public
Markdown guides have `.en.md` and `.cz.md` counterparts with reciprocal links.
Default README/CHANGELOG/CONTRIBUTING files match their English versions.
Czech data in language tests and Czech translation files is intentional.

Preserve explicit pass/fail/review handling, finite request timeouts, no implicit
retries and honest cost reporting. Add a focused regression test for changed
behaviour. For a policy change, version the criteria and evaluate representative
examples separately from software tests. Never describe fixture tests as live model accuracy.

## Pull requests

Explain the problem, resulting behaviour and checks performed. Keep keys,
real article inputs, runtime reports and private working notes out of the patch.
Use synthetic reproductions. Do not include tokens in logs or issue text.

The public API and [agent integration brief](docs/agent-integration.en.md) are
part of the contract; update them when behaviour changes. English is the primary
review language. Windows remains unverified; Linux is the supported test target.
