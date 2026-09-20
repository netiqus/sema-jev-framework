# Using the library

**🇬🇧 English** · [🇨🇿 Česky](api.cz.md)
## One condition

```python
from sema_jev import Gate, Status

gate = Gate("Does `message` explicitly request a refund?")
result = gate.check({"message": "Please refund the duplicate payment."})
if result.status == Status.PASS:
    print("Continue")
elif result.status == Status.FAIL:
    print("Return for correction", result.failed_checks)
else:
    print("Request evidence or review manually", result.review_checks)
```

The default provider is OpenRouter, using `OPENROUTER_API_KEY`. The library does
not discover `.env` files. You can also pass `OpenRouter(api_key=...)`; never put
a real key in source code. The host application supplies credentials.

## Multiple rules and deterministic checks

```python
from sema_jev import Gate, Policy, Rule

policy = Policy(
    "completion",
    version="1",
    rules=(
        Rule.require(
            "scope",
            "Does `diff` implement the requirement in `task`?",
            guidance="Implement the missing part of the requirement.",
        ),
        Rule.require("evidence", "Does `test_output` demonstrate the requested behavior?"),
    ),
    required_fields=("task", "diff", "test_output"),
    required_checks=("build",),
)
gate = Gate(policy)
result = gate.check(
    {"task": "...", "diff": "...", "test_output": "..."},
    checks={"build": True},
)
```

`build` must come from an actual tool, not an agent's assertion. A missing required
key or `None` produces review without a request. An empty string is present;
add a deterministic check if your application rejects it.

`Policy.load(path)` loads JSON schema version 1. Examples are in `policies/`.
Unknown fields are errors, so configuration typos are not silently ignored.

## Rule types

| Constructor | Use |
|---|---|
| `Rule.require(id, instructions)` | Default with an explicit insufficient-evidence option. |
| `Rule.boolean(id, instructions, expected=True)` | Unambiguous binary property, with no separate confidence. |
| `Rule.choose(..., options={...}, accept=(...), reject=(...))` | Custom closed categories; unassigned options produce review. |
| `Rule.rate(..., levels=(...), accept=(2,3), reject=(0,1))` | Described levels; evaluates probability mass in the acceptable levels. |

Defaults `min_probability=0.85` and `min_confidence=0.60` are initial settings only.
Boolean rules have no separate confidence; other rules must meet both thresholds.
`CheckResult.probability` always means support for acceptable outcomes, not the
probability of the selected category or the overall accuracy of a decision.
`guidance` is a repair instruction you supply; the model generates no prose explanation.

## Providers and async

```python
from sema_jev import Gate, TypeSafe

gate = Gate("Does the evidence support the claim?", provider=TypeSafe())
# Reads TYPESAFE_API_KEY only when check() is called.
```
Direct TypeSafe support is offline contract-tested; live verification so far uses OpenRouter.


Use `await gate.acheck(data)` in an asynchronous application. It delegates the
synchronous transport to a thread. Cancelling the awaiting coroutine may leave
a remote request running and billable. Set concurrency limits in the application.
Requests have timeouts, with no automatic retries or provider switching.

## Repair loop

```python
from sema_jev import Gate, run_until_pass

gate = Gate("Does the text contain an explicit greeting?")
result = run_until_pass(
    gate,
    produce=lambda: "Draft text",
    revise=lambda text, decision: "Hello! " + text,
    max_attempts=3,
)
```

`fail` invokes the repair callback; `review` stops immediately. Exhausting the
limit yields `stop_reason=attempt_limit`. The application supplies callbacks;
the library does not invoke a coding LLM or shell. `evidence` maps an output to
Jev input; `checks` obtains fresh deterministic checks after each repair.

## Cost and audit

`result.cost.billed_usd` is the amount returned by the API. `input_usd` and
`output_usd` are calculations from tokens and prices; `calculated_usd` is their sum.
Amounts use `Decimal` and become JSON strings. Missing values are `None`, never
automatically zero. OR prices are cached for at most five minutes and include
their URL and retrieval time. A pricing outage does not invalidate a model answer.
Direct TypeSafe costs are not estimated using OpenRouter prices.

`JsonlAudit(path)` is optional and excludes source texts and keys. A write failure
preserves the original result but sets `audit_error=audit_write_failed`; the
application can stop further processing if required. The audit is not security proof.

## CLI for other applications

```bash
printf '%s' '{"state":{"message":"Please refund the duplicate payment."}}' | sema-jev policies/refund.json
```

Stdout contains decision JSON. Exit codes: 0 pass, 1 fail, 2 review, 3 configuration
or input error. The CLI runs no subsequent command. Live requests are billable.

See [API keys and integration](credentials.en.md) for exact precedence, runtime-file loading and examples for application authors.
