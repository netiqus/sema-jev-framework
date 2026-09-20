# Operations, CI/CD and releases

**🇬🇧 English** · [🇨🇿 Česky](operations.cz.md)
## Source versus runtime

`~/dev/sema-jev-framework` contains source, examples and documentation.
`~/dev-out/sema-jev-framework` contains the runnable copy, `.venv`, `cache/`,
`config/runtime.env` and `artifacts/`. Before each run, `dev.sh` checks source
hygiene and replaces only managed source directories in the runtime. It preserves
`config/` and `artifacts/`. Keep your own data out of runtime `src/`, `tests/`
and other synchronised directories.

`SEMA_OUT_DIR` can override the runtime; it must not point inside source or
`~/dev/`. Clones outside `~/dev` default to a sibling `<name>-out` directory.
`uv.lock` is versioned; CI installs with `--locked`.

The optional real configuration file belongs only in the runtime:

```bash
cp examples/runtime.env.example ~/dev-out/sema-jev-framework/config/runtime.env
chmod 600 ~/dev-out/sema-jev-framework/config/runtime.env
```

Fill it in locally using an editor. Never put a key in a shell argument, example
or commit. The installed library does not read this file; only the development launcher does.

## Verification pipeline

1. Reject runtime artifacts and known credential patterns in source.
2. Ruff lint/format, local documentation links/language pairs, and mypy for public types.
3. Offline tests: decisions, thresholds, local HTTP failures, accounting and loops.
4. Build wheel and sdist, inspect archive contents, run `twine check`.
5. Install the wheel in an empty environment and import outside the repository.
6. Required Linux CI on Python 3.11–3.14, plus a complete check from a clean public export.
   Windows is not part of the verified alpha platform.

Pattern checking is not a universal secret detector. Keep secrets out of source
and export only allowlisted files. PR workflows have no API keys and do not use
`pull_request_target`. Paid live evaluation is separate and explicit.

## CD

The manually triggered `release` workflow accepts a `vX.Y.Z` or prerelease tag such as `v0.2.0a1`, checks that
it matches the package version, runs the same checks and creates a **prerelease draft**
with built archives. The tag must already exist and must be selected as the workflow
ref. It never publishes to PyPI or changes repository visibility.
A private release can be installed into your applications without a public index.

The code is licensed under the [MIT License](../LICENSE). The licence is included
in the wheel, sdist and clean source export. Public repository visibility, PyPI
publication and any trusted publisher remain separate release decisions.

## Clean source export

The wheel contains the Python package; the sdist includes the public source,
examples and docs. `scripts/check_artifacts.py` inspects their manifests.
From a full checkout, create a fresh source snapshot with:

```bash
./dev.sh export --export-dir /path/outside/source/public-source
```

The exporter validates source hygiene, rejects symlinks and unapproved files,
and copies only public directories, named root files and the `ci.yml`,
`release.yml` and `live-evaluation.yml` workflows. Private working notes and
Git history are excluded. It neither publishes nor overwrites an existing export.
CI runs the complete check pipeline from this standalone snapshot.

Keep private development history private. If starting a public repository from
an internal project, initialise a new history from the inspected export.
The [agent integration brief](agent-integration.en.md) is public consumer documentation.

## Optional live evaluation

`./dev.sh evaluate` runs up to 12 billable synthetic checks and saves a runtime
report. The `Optional paid evaluation` workflow runs manually from main only,
requires explicit cost acknowledgement and reads `OPENROUTER_API_KEY` from the
GitHub Actions `live-evaluation` environment. Configure the key in the UI/secret
store, never YAML. Operational failures stop the series. Push and PR workflows
do not call the live API.

`./dev.sh news --lang en` previews the article pair for free.
`./dev.sh news-live --lang en` makes at most two billable requests. Use `cz`
to evaluate the Czech texts directly. See the [example guide](../examples/news/README.en.md).

## Languages

The root README displays the English guide directly. English is primary; Czech is the secondary language. Public guides and release notes have
`.cz.md` / `.en.md` counterparts; demo articles use `.cz.txt` / `.en.txt`.
Every guide links to its counterpart. Unsuffixed legacy guide URLs remain small
English-first language entry pages. `.cz` is the repository filename convention; HTML correctly
uses the language code `cs`. Code, identifiers, comments and default UI text are English. Explicit Czech
presets contain Czech questions; changing the UI language does not translate custom criteria.

The credential contract is documented in [API keys and integration](credentials.en.md).

## Local policy editor

`./dev.sh news-lab --lang en --port 8770` starts the standard-library HTTP workbench
on `127.0.0.1` only. The key comes from the same launcher environment/runtime config;
restart after changing it. The browser receives no key. The server accepts only its
own Host and Origin with a session form token; it exposes named report files, not
the runtime directory or config. It makes no automatic model calls or POST retries.

Runs live in `artifacts/news-lab/runs/<id>/`. A submission marker is written before
calling the provider; replaying the same completed submission returns its result.
An interrupted submission is not automatically retried. An explicit new submission
may incur a new charge. Each run saves `policy.json`, `questions.json`, `report.json`,
article copies and bilingual HTML. A read-only result page cannot itself call the API.
The editor can import/export the same feature policy used by `Gate` (1–10 three-way
choice questions in this demo). See the [methodology guide](article-methodology.en.md).
