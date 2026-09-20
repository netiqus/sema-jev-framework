"""Opt-in live evaluation on authored examples; not a production benchmark."""

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from sema_jev import Gate, OpenRouter, Policy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Authorize billable API requests")
    parser.add_argument("--output", type=Path, default=Path("artifacts/evaluation.json"))
    args = parser.parse_args()
    if not args.live:
        parser.error("Use --live to explicitly authorize API calls")
    source = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    dev_root = (Path.home() / "dev").resolve()
    if dev_root == output or dev_root in output.parents:
        parser.error("Evaluation output must be outside ~/dev")
    dataset = json.loads((source / "evals/cases.json").read_text(encoding="utf-8"))
    provider = OpenRouter()
    decisions = []
    for case in dataset:
        result = Gate(
            Policy.load(source / "policies" / (case["policy"] + ".json")), provider=provider
        ).check(case["state"])
        decisions.append(
            {"id": case["id"], "expected": case["expected"], "decision": result.to_dict()}
        )
        if result.error:
            # Stop on configuration or service errors; don't burn the remaining calls.
            break
    counts = Counter(row["expected"] + "->" + row["decision"]["status"] for row in decisions)
    costs = [row["decision"]["cost"]["billed_usd"] for row in decisions]
    report = {
        "kind": "live_authored_smoke_examples_not_calibration",
        "dataset_size": len(dataset),
        "evaluated": len(decisions),
        "coverage": sum(row["decision"]["status"] != "review" for row in decisions)
        / len(decisions),
        "false_pass_count": sum(
            row["expected"] != "pass" and row["decision"]["status"] == "pass" for row in decisions
        ),
        "false_fail_count": sum(
            row["expected"] != "fail" and row["decision"]["status"] == "fail" for row in decisions
        ),
        "confusion": dict(counts),
        "known_billed_usd": str(sum((Decimal(c) for c in costs if c is not None), Decimal(0))),
        "unknown_cost_calls": sum(c is None for c in costs),
        "results": decisions,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "results"}))
    return int(any(row["decision"]["error"] for row in decisions))


if __name__ == "__main__":
    raise SystemExit(main())
