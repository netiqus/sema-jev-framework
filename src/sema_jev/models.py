"""Stable result types; a decision is never implicitly a boolean."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any


class Status(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    REVIEW = "review"


@dataclass(frozen=True)
class Cost:
    input_tokens: int | None = None
    output_tokens: int | None = None
    input_usd: Decimal | None = None
    output_usd: Decimal | None = None
    billed_usd: Decimal | None = None
    input_rate: Decimal | None = None
    output_rate: Decimal | None = None
    price_source: str | None = None
    price_time: str | None = None
    price_error: str | None = None

    @property
    def calculated_usd(self) -> Decimal | None:
        if self.input_usd is None or self.output_usd is None:
            return None
        return self.input_usd + self.output_usd

    @classmethod
    def no_call(cls) -> Cost:
        return cls(0, 0, Decimal(0), Decimal(0), Decimal(0))

    def to_dict(self) -> dict[str, Any]:
        values = asdict(self)
        values["calculated_usd"] = self.calculated_usd
        return {k: str(v) if isinstance(v, Decimal) else v for k, v in values.items()}


@dataclass(frozen=True)
class CheckResult:
    id: str
    status: Status
    reason: str
    value: str | float | bool | None = None
    probability: float | None = None
    confidence: float | None = None
    probabilities: tuple[tuple[str, float], ...] = ()
    guidance: str = ""


@dataclass(frozen=True)
class Decision:
    status: Status
    checks: tuple[CheckResult, ...]
    policy_id: str
    policy_version: str
    policy_hash: str
    provider: str
    requested_model: str
    actual_model: str | None = None
    request_id: str | None = None
    elapsed_ms: float = 0
    cost: Cost = field(default_factory=Cost)
    error: str | None = None
    audit_error: str | None = None

    @property
    def passed(self) -> bool:
        return self.status == Status.PASS

    @property
    def failed_checks(self) -> tuple[CheckResult, ...]:
        return tuple(c for c in self.checks if c.status == Status.FAIL)

    @property
    def review_checks(self) -> tuple[CheckResult, ...]:
        return tuple(c for c in self.checks if c.status == Status.REVIEW)

    def __bool__(self) -> bool:
        raise TypeError("Use decision.passed or decision.status; REVIEW is not FAIL.")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        result["checks"] = [dict(asdict(c), status=c.status.value) for c in self.checks]
        result["cost"] = self.cost.to_dict()
        return result

    def audit_record(self) -> dict[str, Any]:
        # Deliberately exclude input state, instructions, guidance and raw responses.
        return {
            "schema_version": 1,
            "status": self.status.value,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_hash": self.policy_hash,
            "provider": self.provider,
            "requested_model": self.requested_model,
            "actual_model": self.actual_model,
            "request_id": self.request_id,
            "elapsed_ms": self.elapsed_ms,
            "error": self.error,
            "cost": self.cost.to_dict(),
            "checks": [
                {
                    "id": c.id,
                    "status": c.status.value,
                    "reason": c.reason,
                    "probability": c.probability,
                    "confidence": c.confidence,
                }
                for c in self.checks
            ],
        }
