"""Small integration surface for synchronous and asynchronous applications."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import replace
from typing import Any

from .audit import JsonlAudit
from .engine import aggregate, interpret
from .models import CheckResult, Cost, Decision, Status
from .policy import ConfigurationError, Policy, Rule
from .providers import OpenRouter, Provider
from .wire import ProviderError


class Gate:
    def __init__(
        self,
        policy: Policy | str,
        *,
        provider: Provider | None = None,
        audit: JsonlAudit | None = None,
        max_input_bytes: int = 500_000,
        expected_model: str | None = None,
    ) -> None:
        self.policy = (
            Policy("inline", (Rule.require("requirement", policy),))
            if isinstance(policy, str)
            else policy
        )
        if not isinstance(self.policy, Policy):
            raise ConfigurationError("Use a Policy or a question string")
        if type(max_input_bytes) is not int or max_input_bytes <= 0:
            raise ConfigurationError("max_input_bytes must be a positive integer")
        self.provider = provider if provider is not None else OpenRouter()
        self.audit = audit
        self.max_input_bytes = max_input_bytes
        self.expected_model = expected_model

    def check(self, state: Any, *, checks: dict[str, bool | None] | None = None) -> Decision:
        started = time.perf_counter()
        required = self.policy.required_checks
        supplied = {} if checks is None else checks
        if not isinstance(supplied, dict) or set(supplied) - set(required):
            raise ConfigurationError("Unexpected deterministic checks; declare them in the policy")
        results: list[CheckResult] = []
        for name in required:
            value = supplied.get(name)
            if value is not None and type(value) is not bool:
                raise ConfigurationError("Deterministic checks must be bool or None")
            status = Status.REVIEW if value is None else Status.PASS if value else Status.FAIL
            results.append(
                CheckResult(
                    name,
                    status,
                    "missing_check"
                    if value is None
                    else "deterministic_pass"
                    if value
                    else "deterministic_fail",
                    value,
                )
            )
        if aggregate(tuple(results)) != Status.PASS and results:
            return self._finish(results, started, Cost.no_call())
        if not isinstance(state, (str, dict, list)):
            raise ConfigurationError("state must be JSON text, object or array")
        for name in self.policy.required_fields:
            if not isinstance(state, dict) or name not in state or state[name] is None:
                results.append(CheckResult(name, Status.REVIEW, "missing_evidence"))
        if any(r.status == Status.REVIEW for r in results):
            return self._finish(results, started, Cost.no_call())
        questions = {rule.id: rule.question() for rule in self.policy.rules}
        try:
            raw = json.dumps(
                {"state": state, "questions": questions}, ensure_ascii=False, allow_nan=False
            )
            # Snapshot mutable caller input before handing it to a provider.
            snapshot = json.loads(raw)
        except (TypeError, ValueError, RecursionError):
            raise ConfigurationError("state must be finite, serializable JSON") from None
        if len(raw.encode()) > self.max_input_bytes:
            results.append(CheckResult("input", Status.REVIEW, "input_too_large"))
            return self._finish(results, started, Cost.no_call(), error="input_too_large")
        cost = Cost()
        model = None
        request_id = None
        try:
            evaluation = self.provider.evaluate(snapshot["state"], snapshot["questions"])
            cost = evaluation.cost
            response = evaluation.response
            model = response.get("model")
            if not isinstance(model, str) or not model:
                model = None
                raise ProviderError("invalid_response")
            if self.expected_model is not None and model != self.expected_model:
                raise ProviderError("model_changed")
            request_id = response.get("id")
            if not isinstance(request_id, str):
                request_id = None
            answers = response.get("answers")
            if not isinstance(answers, dict) or set(answers) != set(questions):
                raise ProviderError("invalid_response")
            # Validate every answer before accepting any semantic result.
            semantic = [interpret(rule, answers[rule.id]) for rule in self.policy.rules]
            results.extend(semantic)
        except ProviderError as exc:
            results.extend(
                CheckResult(rule.id, Status.REVIEW, exc.code) for rule in self.policy.rules
            )
            return self._finish(results, started, cost, model, request_id, exc.code)
        return self._finish(results, started, cost, model, request_id)

    async def acheck(self, state: Any, *, checks: dict[str, bool | None] | None = None) -> Decision:
        # Cancelling the awaiting coroutine does not cancel a remote billable call.
        return await asyncio.to_thread(self.check, state, checks=checks)

    def _finish(
        self,
        results: list[CheckResult],
        started: float,
        cost: Cost,
        model: str | None = None,
        request_id: str | None = None,
        error: str | None = None,
    ) -> Decision:
        decision = Decision(
            aggregate(tuple(results)),
            tuple(results),
            self.policy.id,
            self.policy.version,
            self.policy.fingerprint,
            self.provider.name,
            self.provider.model,
            model,
            request_id,
            round((time.perf_counter() - started) * 1000, 3),
            cost,
            error,
        )
        if self.audit is not None:
            try:
                self.audit.write(decision)
            except OSError:
                # Audit availability is observable but never changes the original judgment.
                decision = replace(decision, audit_error="audit_write_failed")
        return decision
