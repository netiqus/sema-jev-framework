"""Importable recipes. Functions run only when called by the consumer."""

from typing import Any

from sema_jev import Gate, Policy, Rule
from sema_jev.models import Decision
from sema_jev.providers import Provider


def news_filter(article: str, provider: Provider) -> Decision:
    policy = Policy(
        "author-stance",
        (
            Rule.require(
                "author_support",
                "Does the author of `article` explicitly endorse the described measure? "
                "Quoted support by someone else does not count as the author's endorsement.",
            ),
        ),
        required_fields=("article",),
    )
    return Gate(policy, provider=provider).check({"article": article})


def completion_gate(
    task: str, diff: str, test_output: str, *, build_passed: bool, provider: Provider
) -> Decision:
    policy = Policy(
        "completion",
        (
            Rule.require("scope", "Does `diff` implement the specific requirement in `task`?"),
            Rule.require(
                "evidence", "Does `test_output` demonstrate the behavior requested in `task`?"
            ),
        ),
        required_fields=("task", "diff", "test_output"),
        required_checks=("build",),
    )
    return Gate(policy, provider=provider).check(
        {"task": task, "diff": diff, "test_output": test_output}, checks={"build": build_passed}
    )


async def async_filter(data: Any, gate: Gate) -> Decision:
    return await gate.acheck(data)
