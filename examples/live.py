"""One billable synthetic request; reads OPENROUTER_API_KEY from the environment."""

import json

from sema_jev import Gate, Policy, Rule

policy = Policy(
    "synthetic-refund",
    (Rule.require("refund", "Does `message` explicitly request a refund?"),),
    required_fields=("message",),
)
result = Gate(policy).check({"message": "Please refund the duplicate payment."})
print(json.dumps(result.to_dict(), indent=2))
raise SystemExit(0 if result.passed else 2)
