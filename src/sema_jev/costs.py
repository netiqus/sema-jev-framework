"""USD accounting distinguishes measured billing from a catalogue estimate."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import Cost


def amount(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
        return number if number.is_finite() and number >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def _count(value: Any) -> int | None:
    return value if type(value) is int and value >= 0 else None


@dataclass(frozen=True)
class Price:
    input_rate: Decimal | None = None
    output_rate: Decimal | None = None
    source: str | None = None
    fetched_at: str | None = None
    error: str | None = None


def calculate(usage: Any, price: Price) -> Cost:
    usage = usage if isinstance(usage, dict) else {}
    inp = _count(usage.get("input_tokens", usage.get("prompt_tokens")))
    out = _count(usage.get("output_tokens", usage.get("completion_tokens")))
    return Cost(
        inp,
        out,
        inp * price.input_rate if inp is not None and price.input_rate is not None else None,
        out * price.output_rate if out is not None and price.output_rate is not None else None,
        amount(usage.get("cost")),
        price.input_rate,
        price.output_rate,
        price.source,
        price.fetched_at,
        price.error,
    )
