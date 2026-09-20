"""Strict, size-bounded JSON HTTP transport with no credential redirects."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from http.client import HTTPException
from typing import Any


class ProviderError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ValueError("Non-finite JSON value")


def decode_json(raw: bytes) -> Any:
    return json.loads(raw, object_pairs_hook=_unique, parse_constant=_reject_constant)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: Any, msg: Any, headers: Any, newurl: Any
    ) -> None:
        return None


class JsonTransport:
    def request(
        self, url: str, *, headers: dict[str, str], payload: dict[str, Any] | None, timeout: float
    ) -> dict[str, Any]:
        body = (
            None
            if payload is None
            else json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()
        )
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.build_opener(_NoRedirect()).open(req, timeout=timeout) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ProviderError("response_too_large")
            parsed = decode_json(raw)
            if not isinstance(parsed, dict):
                raise ProviderError("invalid_response")
            return parsed
        except urllib.error.HTTPError as exc:
            code = {
                401: "authentication",
                403: "permission",
                429: "rate_limit",
                529: "overloaded",
            }.get(exc.code, "http_error")
            exc.close()
            raise ProviderError(code) from None
        except TimeoutError:
            raise ProviderError("timeout") from None
        except (urllib.error.URLError, OSError, HTTPException):
            raise ProviderError("network") from None
        except (ValueError, UnicodeError):
            raise ProviderError("invalid_response") from None
