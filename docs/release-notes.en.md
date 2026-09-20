# Sema Jev Framework 0.2.0a2

**🇬🇧 English** · [🇨🇿 Česky](release-notes.cz.md)

First public experimental alpha of the **netiqus** project. This release packages
semantic gates, a practical article lab and an English-first integration guide
under the MIT licence. Python 3.11+; no runtime dependencies. Not published on PyPI.

## Included

- Typed pass/fail/review decisions, versioned policies, deterministic checks,
  async calls, a bounded repair loop, JSON CLI, audit metadata and cost accounting.
- A local article/criteria editor with free request inspection, explicit paid runs,
  immutable results and policy export. Fictional articles and presets in EN/CZ.
- English-default README, evaluation and contributor guides, with Czech counterparts.
- A public agent integration brief requiring no knowledge of the Jev wire format.
- Allowlisted source export with Linux CI and manual draft/evaluation workflows.
  Clean-export and installed-wheel checks are part of the release pipeline.

## Verification scope

Linux Python 3.11–3.14 is verified by offline CI. Live checks have used OpenRouter.
The direct TypeSafe adapter is contract-tested offline but not verified live.
Windows remains unverified. Default thresholds and example policies are not
calibrated production methodologies; see [limitations](limitations.en.md).

Install from a source checkout or the matching wheel using the [README](../README.md).
The release workflow prepares a draft for maintainer review. Publishing that draft
is a separate step; the workflow does not publish to PyPI.
