"""Optional bounded repair loop; callbacks own all application side effects."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .gate import Gate
from .models import Decision, Status
from .policy import ConfigurationError


@dataclass(frozen=True)
class WorkflowResult:
    value: Any
    decisions: tuple[Decision, ...]
    stop_reason: str

    @property
    def passed(self) -> bool:
        return self.decisions[-1].passed

    @property
    def known_cost_usd(self) -> Decimal:
        return sum(
            (d.cost.billed_usd for d in self.decisions if d.cost.billed_usd is not None), Decimal(0)
        )

    @property
    def unknown_cost_calls(self) -> int:
        return sum(d.cost.billed_usd is None for d in self.decisions)

    def __bool__(self) -> bool:
        raise TypeError("Use result.passed explicitly")


def run_until_pass(
    gate: Gate,
    produce: Callable[[], Any],
    revise: Callable[[Any, Decision], Any],
    *,
    max_attempts: int = 3,
    evidence: Callable[[Any], Any] | None = None,
    checks: Callable[[Any], dict[str, bool | None]] | None = None,
) -> WorkflowResult:
    if type(max_attempts) is not int or max_attempts < 1:
        raise ConfigurationError("max_attempts must be a positive integer")
    value = produce()
    decisions: list[Decision] = []
    for attempt in range(max_attempts):
        decision = gate.check(
            evidence(value) if evidence else value, checks=checks(value) if checks else None
        )
        decisions.append(decision)
        if decision.status != Status.FAIL:
            return WorkflowResult(
                value, tuple(decisions), "passed" if decision.passed else "review_required"
            )
        if attempt + 1 < max_attempts:
            value = revise(value, decision)
    return WorkflowResult(value, tuple(decisions), "attempt_limit")
