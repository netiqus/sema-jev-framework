"""JSON stdin/stdout bridge for applications outside Python."""

from __future__ import annotations

import argparse
import json
import sys

from . import Gate, Policy, Status, TypeSafe
from .policy import ConfigurationError
from .wire import decode_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate JSON evidence against a semantic policy")
    parser.add_argument("policy", help="Path to a versioned policy JSON")
    parser.add_argument("--provider", choices=("openrouter", "typesafe"), default="openrouter")
    args = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(500_001)
        if len(raw) > 500_000:
            raise ConfigurationError("Input exceeds 500000 bytes")
        payload = decode_json(raw)
        if (
            not isinstance(payload, dict)
            or "state" not in payload
            or set(payload) - {"state", "checks"}
        ):
            raise ConfigurationError('Expected {"state": ..., "checks": {...}}')
        provider = TypeSafe() if args.provider == "typesafe" else None
        result = Gate(Policy.load(args.policy), provider=provider).check(
            payload["state"], checks=payload.get("checks")
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False))
        return {Status.PASS: 0, Status.FAIL: 1, Status.REVIEW: 2}[result.status]
    except (ConfigurationError, ValueError, OSError):
        print(json.dumps({"error": "invalid_configuration_or_input"}), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
