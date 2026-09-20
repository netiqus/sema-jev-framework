import json
import runpy
from pathlib import Path

from sema_jev import FakeProvider, Gate, Policy, Status


def answer(option="supported"):
    probabilities = dict.fromkeys(("supported", "contradicted", "insufficient"), 0.01)
    probabilities[option] = 0.98
    return {"type": "choice", "choice": option, "confidence": 0.95, "probabilities": probabilities}


def test_documented_integration_recipes():
    recipes = runpy.run_path("examples/integrations.py")
    d = recipes["news_filter"]("synthetic article", FakeProvider({"author_support": answer()}))
    assert d.passed
    provider = FakeProvider({"scope": answer(), "evidence": answer()})
    d = recipes["completion_gate"](
        "task", "diff", "test output", build_passed=False, provider=provider
    )
    assert d.status == Status.FAIL and provider.calls == 0
    d = recipes["completion_gate"](
        "task", "diff", "test output", build_passed=True, provider=provider
    )
    assert d.passed and provider.calls == 1


def test_offline_repair_example():
    assert runpy.run_path("examples/offline.py")["result"].passed


def test_example_policies_and_evaluation_dataset_contract():
    cases = json.loads(Path("evals/cases.json").read_text(encoding="utf-8"))
    assert len({case["id"] for case in cases}) == len(cases)
    for path in Path("policies").glob("*.json"):
        policy = Policy.load(path)
        assert Policy.from_dict(policy.to_dict()) == policy
    for case in cases:
        policy = Policy.load("policies/" + case["policy"] + ".json")
        assert set(policy.required_fields) <= set(case["state"])
        assert case["expected"] in ("pass", "fail", "review")
        responses = {rule.id: answer("insufficient") for rule in policy.rules}
        assert (
            Gate(policy, provider=FakeProvider(responses)).check(case["state"]).status
            == Status.REVIEW
        )
