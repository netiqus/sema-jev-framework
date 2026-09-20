"""Offline integration example. All model answers here are explicit fixtures."""

from sema_jev import FakeProvider, Gate, Policy, Rule, run_until_pass


def answer(option: str) -> dict:
    probabilities = dict.fromkeys(("supported", "contradicted", "insufficient"), 0.01)
    probabilities[option] = 0.98
    return {
        "requirement": {
            "type": "choice",
            "choice": option,
            "probabilities": probabilities,
            "confidence": 0.95,
        }
    }


policy = Policy(
    "completion",
    (
        Rule.require(
            "requirement",
            "Does the output include a greeting?",
            guidance="Add the missing greeting.",
        ),
    ),
)
gate = Gate(policy, provider=FakeProvider([answer("contradicted"), answer("supported")]))
result = run_until_pass(
    gate, produce=lambda: "Draft", revise=lambda text, decision: "Hello! " + text
)
assert result.passed and len(result.decisions) == 2
print("OFFLINE FIXTURES ONLY:", result.stop_reason, "attempts:", len(result.decisions))
print(result.decisions[-1].to_dict())
