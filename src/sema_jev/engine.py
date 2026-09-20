"""Pure response validation and deterministic decision composition."""

from __future__ import annotations

import math
from typing import Any

from .models import CheckResult, Status
from .policy import Rule
from .wire import ProviderError


def _number(value: Any, high: float = 1) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProviderError("invalid_response")
    if not math.isfinite(value) or not 0 <= value <= high:
        raise ProviderError("invalid_response")
    return float(value)


def interpret(rule: Rule, answer: Any) -> CheckResult:
    if not isinstance(answer, dict) or answer.get("type") != rule.kind:
        raise ProviderError("invalid_response")
    confidence = None
    if rule.kind == "noul":
        value: str | float = _number(answer.get("noul"))
        probabilities = {"yes": float(value), "no": 1 - float(value)}
    else:
        confidence = _number(answer.get("confidence"))
        raw = answer.get("probabilities")
        keys = dict(rule.criteria)
        if not isinstance(raw, dict) or set(raw) != set(keys):
            raise ProviderError("invalid_response")
        probabilities = {k: _number(v) for k, v in raw.items()}
        # Some providers round distributions to two decimal places.
        total = sum(probabilities.values())
        if not math.isclose(total, 1, abs_tol=0.02):
            raise ProviderError("invalid_response")
        # Normalize accepted rounding before applying thresholds: disjoint
        # accept/reject sets must never both exceed a majority.
        probabilities = {key: probability / total for key, probability in probabilities.items()}
        if rule.kind == "choice":
            chosen = answer.get("choice")
            if not isinstance(chosen, str) or chosen not in probabilities:
                raise ProviderError("invalid_response")
            value = chosen
            if probabilities[value] + 0.011 < max(probabilities.values()):
                raise ProviderError("invalid_response")
        else:
            value = _number(answer.get("score"), len(keys) - 1)
            legend = answer.get("legend")
            if not isinstance(legend, dict) or legend != keys:
                raise ProviderError("invalid_response")
            # Use the distribution for decisions, never the potentially ambiguous mean.
    yes = min(1.0, sum(probabilities[k] for k in rule.accept))
    no = min(1.0, sum(probabilities[k] for k in rule.reject))
    if confidence is not None and confidence < rule.min_confidence:
        status, reason = Status.REVIEW, "low_confidence"
    elif yes >= rule.min_probability:
        status, reason = Status.PASS, "criterion_met"
    elif no >= rule.min_probability:
        status, reason = Status.FAIL, "criterion_not_met"
    else:
        status, reason = Status.REVIEW, "insufficient_support"
    return CheckResult(
        rule.id, status, reason, value, yes, confidence, tuple(probabilities.items()), rule.guidance
    )


def aggregate(checks: tuple[CheckResult, ...]) -> Status:
    if not checks:
        return Status.REVIEW
    if any(c.status == Status.FAIL for c in checks):
        return Status.FAIL
    if any(c.status == Status.REVIEW for c in checks):
        return Status.REVIEW
    return Status.PASS
