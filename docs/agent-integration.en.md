# Agent integration brief

**🇬🇧 English** · [🇨🇿 Česky](agent-integration.cz.md) · [Project](../README.md)

Use this page when asking a coding agent to add Sema to an existing application.
It describes the public contract and contains no maintainer-specific workflow.
The application remains responsible for permissions, secrets and side effects.

## Copy into an integration task

> Integrate `sema_jev` at the selected decision point. Reuse `Gate`, `Policy`,
> `Rule` and `Status`; do not write another Jev HTTP client or probability parser.
> Keep exact validation and authorisation in the host application. Define one
> versioned policy with explicit requirements and insufficient-evidence handling.
> Reuse the gate, call `check` (or `await acheck`) and route PASS, FAIL and REVIEW
> separately. Never use `if decision`, silently retry until pass or treat an API
> error as approval. Read this guide and `docs/api.en.md`; inspect implementation
> only when needed. Test all routes with `FakeProvider` before a separately
> authorised live check. Report which checks were simulated and which were live.

## Minimal integration

Install the package in the application's environment using the
[installation instructions](../README.md#quick-start). Credentials come from the
host's environment or secret store, not policy JSON or source files.

```python
from sema_jev import Gate, Status

refund_gate = Gate("Does `message` explicitly request a refund?")


def route_message(message: str) -> str:
    decision = refund_gate.check({"message": message})
    if decision.status == Status.PASS:
        return "refund_queue"
    if decision.status == Status.FAIL:
        return "general_queue"
    return "review_queue"
```

The default provider reads `OPENROUTER_API_KEY` at request time. For keys already
managed by the app, pass `provider=OpenRouter(api_key=runtime_key)` to `Gate`.
Explicit keys take precedence; an explicitly empty key does not fall back to env.
No credential file is discovered by the installed library.

## Policy and result contract

- `Rule.require(id, instructions)` includes support, contradiction and insufficient
  evidence. Reference actual input field names and define what counts. Use separate
  questions for independent requirements; a vague “is everything correct?” is not a policy.
- `Policy(..., required_fields=(...), required_checks=(...))` declares required data
  and deterministic checks. Supply real tool outcomes via `gate.check(data, checks=...)`.
  Failed or missing fixed checks prevent a model request.
- `pass` requires every check to pass. A definite failure produces `fail` even if
  another check is uncertain. Otherwise uncertainty produces `review`.
- `decision.checks` contains individual outcomes; `failed_checks` and `review_checks`
  expose subsets. `decision.error` is a provider error code. Invalid local policy
  configuration raises `ConfigurationError`.
- `guidance` is your predefined repair text, not a model-written explanation.
  `run_until_pass` revises after fail, stops on review and has a finite attempt limit.
- Confidence is not the probability of “yes”. `CheckResult.probability` is support
  for acceptable outcomes. Default thresholds require domain validation.
- Costs are `Decimal` values; `None` means unknown. Preserve unknown-cost counts.
  `decision.to_dict()` is JSON-friendly and includes policy hash and model identity.
- `acheck` uses a thread; cancelling the await does not guarantee cancelled billing.
  Bound concurrency and configure provider timeouts in the application.

## Offline verification

Use fixtures to exercise the application branches. This example explicitly
simulates insufficient evidence; it does not call a model:

```python
from sema_jev import FakeProvider, Gate, Status

provider = FakeProvider({
    "requirement": {
        "type": "choice",
        "choice": "insufficient",
        "probabilities": {"supported": 0.01, "contradicted": 0.01, "insufficient": 0.98},
        "confidence": 0.98,
    }
})
result = Gate("Does the evidence establish completion?", provider=provider).check({})
assert result.status == Status.REVIEW
assert not result.passed
```

Also cover pass, fail, provider failure and a failed fixed check. The latter must
not call the provider. Never present this as validation of Jev's semantic accuracy.
Evaluate a versioned policy on separately labelled domain examples before deployment.

## Reuse a policy from the article lab

Load its exported JSON through `Policy.load(path)` and submit `{"article": text}`.
The export contains the actual criteria; do not add an invented hidden prompt.
The framework prepends its documented evidence-only instruction.

Read the individual feature outcomes. Aggregate pass/fail is not an article-quality
score. The demo's `routing_rule` is separate application logic and is not included
in the policy export. Decide the host application's routes explicitly.

[API](api.en.md) · [Credentials](credentials.en.md) · [Methodology](methodology.en.md) · [Recipes](../examples/integrations.py)
