import asyncio
import json
from dataclasses import replace
from decimal import Decimal

import pytest

from sema_jev import (
    ConfigurationError,
    FakeProvider,
    Gate,
    JsonlAudit,
    Policy,
    Rule,
    Status,
    run_until_pass,
)
from sema_jev.costs import Price, calculate
from sema_jev.providers import Evaluation
from sema_jev.wire import ProviderError


def choice(option="supported", confidence=0.95):
    probabilities = dict.fromkeys(("supported", "contradicted", "insufficient"), 0.01)
    probabilities[option] = 0.98
    return {
        "type": "choice",
        "choice": option,
        "probabilities": probabilities,
        "confidence": confidence,
    }


def gate(answer=None, **kwargs):
    return Gate(
        "Does the evidence meet the requirement?",
        provider=FakeProvider({"requirement": choice() if answer is None else answer}),
        **kwargs,
    )


@pytest.mark.parametrize(
    "option,status",
    [("supported", Status.PASS), ("contradicted", Status.FAIL), ("insufficient", Status.REVIEW)],
)
def test_explicit_evidence_states(option, status):
    result = gate(choice(option)).check("synthetic")
    assert result.status == status
    assert result.passed is (status == Status.PASS)
    with pytest.raises(TypeError):
        bool(result)


def test_confidence_is_not_the_yes_probability():
    result = gate(choice("contradicted", 1)).check("synthetic")
    assert result.status == Status.FAIL
    assert result.checks[0].probability == 0.01
    assert gate(choice("supported", 0.1)).check("synthetic").status == Status.REVIEW


@pytest.mark.parametrize(
    "prob,status",
    [
        (1, Status.PASS),
        (0.85, Status.PASS),
        (0.5, Status.REVIEW),
        (0.10, Status.FAIL),
        (0, Status.FAIL),
    ],
)
def test_boolean_thresholds(prob, status):
    policy = Policy("boolean", (Rule.boolean("x", "Is it a request?"),))
    provider = FakeProvider({"x": {"type": "noul", "noul": prob}})
    assert Gate(policy, provider=provider).check("synthetic").status == status


def test_boolean_false_expectation():
    rule = Rule.boolean("x", "Does it contain insults?", expected=False)
    d = Gate(
        Policy("p", (rule,)), provider=FakeProvider({"x": {"type": "noul", "noul": 0.01}})
    ).check("x")
    assert d.passed and d.checks[0].confidence is None


def test_score_does_not_pass_a_bimodal_mean():
    rule = Rule.rate(
        "quality",
        "Rate quality",
        levels=("bad", "poor", "good", "excellent"),
        accept=(2, 3),
        reject=(0, 1),
        min_confidence=0,
    )
    response = {
        "type": "score",
        "score": 1.5,
        "legend": dict(rule.criteria),
        "probabilities": {"0": 0.5, "1": 0, "2": 0, "3": 0.5},
        "confidence": 0.9,
    }
    d = Gate(Policy("p", (rule,)), provider=FakeProvider({"quality": response})).check("x")
    assert d.status == Status.REVIEW
    response["probabilities"] = {"0": 0, "1": 0, "2": 0.02, "3": 0.98}
    response["score"] = 2.98
    assert (
        Gate(Policy("p", (rule,)), provider=FakeProvider({"quality": response})).check("x").passed
    )


def test_partial_rule_failure_overrides_other_pass():
    p = Policy("all", (Rule.require("a", "A?"), Rule.require("b", "B?")))
    d = Gate(p, provider=FakeProvider({"a": choice(), "b": choice("contradicted")})).check("x")
    assert d.status == Status.FAIL and [c.id for c in d.failed_checks] == ["b"]


@pytest.mark.parametrize(
    "answer",
    [
        None,
        {},
        {"type": "noul", "noul": 1},
        {"type": "choice", "choice": "supported", "confidence": 1, "probabilities": {}},
        {
            "type": "choice",
            "choice": "supported",
            "confidence": float("nan"),
            "probabilities": {"supported": 1, "contradicted": 0, "insufficient": 0},
        },
        {
            "type": "choice",
            "choice": "supported",
            "confidence": 1,
            "probabilities": {"supported": True, "contradicted": 0, "insufficient": 0},
        },
        {
            "type": "choice",
            "choice": "supported",
            "confidence": 1,
            "probabilities": {"supported": 0.2, "contradicted": 0.7, "insufficient": 0.1},
        },
        {
            "type": "choice",
            "choice": "supported",
            "confidence": 1,
            "probabilities": {"supported": 1, "contradicted": 1, "insufficient": 0},
        },
    ],
)
def test_malformed_answer_never_passes(answer):
    provider = FakeProvider({"requirement": answer})
    d = Gate("Met?", provider=provider).check("x")
    assert d.status == Status.REVIEW and d.error == "invalid_response"


def test_missing_extra_answers_and_model_change():
    for answers in ({}, {"requirement": choice(), "surprise": choice()}):
        assert Gate("Met?", provider=FakeProvider(answers)).check("x").status == Status.REVIEW
    assert gate(expected_model="pinned/version").check("x").error == "model_changed"


def test_network_failure_is_visible_and_cost_unknown():
    class Broken:
        name, model = "broken", "test"

        def evaluate(self, state, questions):
            raise ProviderError("timeout")

    d = Gate("Met?", provider=Broken()).check("x")
    assert d.status == Status.REVIEW and d.error == "timeout"
    assert d.cost.billed_usd is None


def test_invalid_answers_retain_incurred_cost():
    class Invalid:
        name, model = "broken", "test"

        def evaluate(self, state, questions):
            return Evaluation({"model": "test", "answers": {}}, calculate({"cost": ".01"}, Price()))

    assert Gate("Met?", provider=Invalid()).check("x").cost.billed_usd == Decimal(".01")


def test_deterministic_and_evidence_checks_skip_provider():
    p = Policy(
        "p", (Rule.require("x", "Met?"),), required_checks=("build",), required_fields=("diff",)
    )
    provider = FakeProvider({})
    g = Gate(p, provider=provider)
    assert g.check({}, checks={"build": False}).status == Status.FAIL
    assert g.check({}).status == Status.REVIEW
    assert g.check({}, checks={"build": True}).checks[-1].reason == "missing_evidence"
    assert provider.calls == 0
    with pytest.raises(ConfigurationError):
        g.check({}, checks={"build": "yes"})
    with pytest.raises(ConfigurationError):
        g.check({}, checks={"surprise": True})


def test_input_size_no_call_no_cost():
    g = gate(max_input_bytes=1)
    d = g.check("long")
    assert d.error == "input_too_large" and d.cost.billed_usd == 0
    assert g.provider.calls == 0


@pytest.mark.parametrize("state", [None, 1, True, {"x": float("nan")}, {"x": object()}])
def test_invalid_state_is_local_error(state):
    with pytest.raises(ConfigurationError):
        gate().check(state)


def test_policy_roundtrip_and_hash(tmp_path):
    p = Policy(
        "test", (Rule.require("r", "Does `text` mention a refund?"),), required_fields=("text",)
    )
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(p.to_dict()))
    assert Policy.load(path) == p
    assert replace(p, version="2").fingerprint != p.fingerprint
    assert (
        replace(p, rules=(replace(p.rules[0], min_probability=0.9),)).fingerprint != p.fingerprint
    )
    bad = p.to_dict()
    bad["typo"] = "not ignored"
    with pytest.raises(ConfigurationError):
        Policy.from_dict(bad)
    path.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ConfigurationError):
        Policy.load(path)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Rule.boolean("x", "x?", min_probability=0.5),
        lambda: Rule.require("bad id", "x?"),
        lambda: Rule.require("x", ""),
        lambda: Rule.require("x", "x?", min_confidence=float("inf")),
        lambda: Policy("x", ()),
        lambda: Policy("x", (Rule.require("x", "x?"),), required_checks=("x",)),
        lambda: Rule.choose("x", "x?", options={"a": "A", "b": "B"}, accept=("a",), reject=("a",)),
    ],
)
def test_configuration_errors(factory):
    with pytest.raises(ConfigurationError):
        factory()


def test_cost_exact_and_missing_not_zero():
    c = calculate(
        {"input_tokens": 4111, "output_tokens": 36, "cost": 0.000172662},
        Price(Decimal(".000000042"), Decimal(0)),
    )
    assert c.input_usd == c.billed_usd == c.calculated_usd == Decimal(".000172662")
    assert c.output_usd == 0
    assert calculate({}, Price()).billed_usd is None
    assert calculate({"cost": 0}, Price()).billed_usd == 0
    assert calculate({"cost": "NaN", "input_tokens": True}, Price()).input_tokens is None
    assert calculate({"cost": "NaN"}, Price()).billed_usd is None


def test_async_matches_sync():
    assert asyncio.run(gate().acheck("x")).passed


def test_metadata_audit_excludes_input(tmp_path):
    path = tmp_path / "audit.jsonl"
    d = gate(audit=JsonlAudit(path)).check("sensitive article content")
    text = path.read_text()
    assert "sensitive article" not in text and "instructions" not in text
    assert json.loads(text)["policy_hash"] == d.policy_hash


def test_audit_failure_visible(tmp_path):
    path = tmp_path / "directory"
    path.mkdir()
    d = gate(audit=JsonlAudit(path)).check("x")
    assert d.passed and d.audit_error == "audit_write_failed"


def test_bounded_repair_and_review_stop():
    provider = FakeProvider([{"requirement": choice("contradicted")}, {"requirement": choice()}])
    g = Gate("Met?", provider=provider)
    result = run_until_pass(g, lambda: "first", lambda value, d: "fixed", max_attempts=2)
    assert result.passed and result.value == "fixed" and result.known_cost_usd == 0
    called = []
    result = run_until_pass(gate(choice("insufficient")), lambda: "x", lambda *a: called.append(1))
    assert result.stop_reason == "review_required" and called == []
    result = run_until_pass(
        gate(choice("contradicted")), lambda: "x", lambda *a: "retry", max_attempts=1
    )
    assert result.stop_reason == "attempt_limit"


def test_rounded_distribution_cannot_pass_both_sides():
    rule = Rule.choose(
        "r",
        "Select",
        options={"a": "A", "b": "B"},
        accept=("a",),
        reject=("b",),
        min_probability=0.501,
    )
    answer = {
        "type": "choice",
        "choice": "a",
        "confidence": 1,
        "probabilities": {"a": 0.509, "b": 0.509},
    }
    d = Gate(Policy("rounding", (rule,)), provider=FakeProvider({"r": answer})).check("test")
    assert d.status == Status.REVIEW
    assert sum(dict(d.checks[0].probabilities).values()) == 1
