"""Provider adapters. Imports never make requests or discover credentials."""

from __future__ import annotations

import copy
import math
import os
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import quote

from .costs import Price, amount, calculate
from .models import Cost
from .policy import ConfigurationError
from .wire import JsonTransport, ProviderError


@dataclass(frozen=True)
class Evaluation:
    response: dict[str, Any]
    cost: Cost


class Provider(Protocol):
    name: str
    model: str

    def evaluate(self, state: Any, questions: dict[str, Any]) -> Evaluation: ...


class OpenRouter:
    name = "openrouter"
    endpoint = "https://openrouter.ai/api/alpha/decisions"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "typesafe/jev-1.13",
        timeout: float = 30,
        pricing: bool = True,
        transport: JsonTransport | None = None,
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ConfigurationError("model must be non-empty")
        if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise ConfigurationError("timeout must be finite and positive")
        self.model = model
        self.timeout = timeout
        self._key = api_key
        self._pricing = pricing
        self._transport = transport or JsonTransport()
        self._price = Price(error="unavailable")
        self._price_until = 0.0
        self._price_lock = threading.Lock()

    def _api_key(self) -> str:
        key = self._key if self._key is not None else os.environ.get("OPENROUTER_API_KEY", "")
        if not isinstance(key, str) or not key.strip():
            raise ProviderError("missing_api_key")
        return key.strip()

    def _get_price(self) -> Price:
        if not self._pricing:
            return Price(error="pricing_disabled")
        with self._price_lock:
            if time.monotonic() < self._price_until:
                return self._price
            url = "https://openrouter.ai/api/v1/model/" + quote(self.model, safe="/")
            try:
                response = self._transport.request(
                    url, headers={}, payload=None, timeout=min(self.timeout, 8)
                )
                raw = response["data"]["pricing"]
                self._price = Price(
                    amount(raw.get("prompt")),
                    amount(raw.get("completion")),
                    url,
                    datetime.now(UTC).isoformat(),
                )
                self._price_until = time.monotonic() + 300
            except (ProviderError, KeyError, TypeError, AttributeError):
                self._price = Price(source=url, error="pricing_unavailable")
                self._price_until = time.monotonic() + 30
            return self._price

    def evaluate(self, state: Any, questions: dict[str, Any]) -> Evaluation:
        # No automatic POST retries: an ambiguous failure may already be billable.
        key = self._api_key()
        response = self._transport.request(
            self.endpoint,
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            payload={"model": self.model, "state": state, "questions": questions},
            timeout=self.timeout,
        )
        return Evaluation(response, calculate(response.get("usage"), self._get_price()))


class TypeSafe(OpenRouter):
    name = "typesafe"
    endpoint = "https://api.typesafe.ai/v1/systemone"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "jev-1.13",
        timeout: float = 30,
        transport: JsonTransport | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key, model=model, timeout=timeout, pricing=False, transport=transport
        )

    def _api_key(self) -> str:
        key = self._key if self._key is not None else os.environ.get("TYPESAFE_API_KEY", "")
        if not isinstance(key, str) or not key.strip():
            raise ProviderError("missing_api_key")
        return key.strip()


class FakeProvider:
    """Explicit offline fixture. It never falls back to a live API."""

    name = "fake"
    model = "fake/fixture"

    def __init__(self, answers: dict[str, Any] | list[dict[str, Any]]) -> None:
        self._answers = copy.deepcopy(answers if isinstance(answers, list) else [answers])
        self.calls = 0
        self._lock = threading.Lock()

    def evaluate(self, state: Any, questions: dict[str, Any]) -> Evaluation:
        with self._lock:
            if self.calls >= len(self._answers):
                raise ProviderError("fixture_exhausted")
            answers = copy.deepcopy(self._answers[self.calls])
            self.calls += 1
        return Evaluation(
            {
                "model": self.model,
                "answers": answers,
                "usage": {"input_tokens": 0, "output_tokens": 0, "cost": 0},
            },
            Cost.no_call(),
        )
