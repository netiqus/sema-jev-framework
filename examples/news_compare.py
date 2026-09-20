"""Two articles, one policy: optional live evaluation and a bilingual local report."""

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal
from html import escape
from pathlib import Path
from typing import Any

from sema_jev import ConfigurationError, Gate, Policy
from sema_jev.providers import Provider

ASSETS = Path(__file__).resolve().parent / "news"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_preset(name: str = "event", language: str = "en") -> dict[str, Any]:
    if name not in ("event", "general") or language not in ("en", "cz"):
        raise ConfigurationError("Unknown preset or preset language")
    stem = "policy" if name == "event" else "policy.general"
    return load_json(ASSETS / f"{stem}.{language}.json")


def feature_axes(rules: list[dict[str, Any]], ui: dict[str, Any]) -> dict[str, list[str]]:
    """Only attach preset labels when the submitted wording still matches a preset."""
    originals = [
        rule
        for name in ("event", "general")
        for language in ("en", "cz")
        for rule in load_preset(name, language)["rules"]
    ]
    return {
        rule["id"]: ui["axes"].get(rule["id"], [rule["id"], rule["instructions"]])
        if any(
            all(rule[key] == original[key] for key in ("id", "instructions", "criteria"))
            for original in originals
        )
        else [rule["id"], rule["instructions"]]
        for rule in rules
    }


def route(
    decision: dict[str, Any] | None,
    policy: Policy | None = None,
    routing_rule: str | None = "authorial_persuasion",
) -> str:
    """Route by observed authorship, never by political approval or an aggregate FAIL."""
    if decision is None:
        return "not_measured"
    checks = {check["id"]: check for check in decision["checks"]}
    required = {rule.id for rule in (policy or Policy.load(ASSETS / "policy.json")).rules}
    if decision["error"] or not required <= checks.keys():
        return "review_queue"
    if any(check["status"] == "review" for check in checks.values()):
        return "review_queue"
    if routing_rule is None or routing_rule not in checks:
        return "profile_ready"
    return "commentary_queue" if checks[routing_rule]["status"] == "pass" else "reporting_queue"


def validate_news_policy(policy: Policy) -> None:
    """Keep the teaching UI's present/absent vocabulary honest for custom policies."""
    if not 1 <= len(policy.rules) <= 10:
        raise ConfigurationError("Use between one and ten criteria")
    if policy.required_fields != ("article",) or policy.required_checks:
        raise ConfigurationError("This example requires only the article field and no fixed checks")
    for rule in policy.rules:
        if (
            rule.kind != "choice"
            or set(dict(rule.criteria)) != {"present", "absent", "unclear"}
            or rule.accept != ("present",)
            or rule.reject != ("absent",)
        ):
            raise ConfigurationError("This example uses choice: present / absent / unclear")


def prepare_articles(texts: tuple[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "id": name,
            "text": text,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "words": len(text.split()),
            "decision": None,
        }
        for name, text in zip(("a", "b"), texts, strict=True)
    ]


def evaluate_articles(
    articles: list[dict[str, Any]],
    provider: Provider | None = None,
    *,
    policy: Policy | None = None,
) -> None:
    policy = policy or Policy.load(ASSETS / "policy.json")
    validate_news_policy(policy)
    gate = Gate(policy, provider=provider)
    for article in articles:
        # Labels, filenames, editorial expectations and the other article never reach the model.
        decision = gate.check({"article": article["text"]})
        article["decision"] = decision.to_dict()
        if decision.error:
            break


def summarize_costs(articles: list[dict[str, Any]]) -> dict[str, Any]:
    costs = [a["decision"]["cost"] for a in articles if a["decision"] is not None]
    summary: dict[str, Any] = {"assessments": len(costs)}
    for field in ("billed_usd", "calculated_usd"):
        known = [Decimal(cost[field]) for cost in costs if cost[field] is not None]
        summary[field] = {
            "known_sum": str(sum(known, Decimal(0))),
            "unknown_count": len(costs) - len(known),
        }
    return summary


def percent(value: float | None, unknown: str) -> str:
    return unknown if value is None else f"{value:.1%}"


def render_methodology(report: dict[str, Any], ui: dict[str, Any], policy: Policy) -> str:
    questions = report.get("questions") or {rule.id: rule.question() for rule in policy.rules}
    axes = feature_axes(policy.to_dict()["rules"], ui)
    cards = []
    for rule in policy.rules:
        options = "".join(
            f"<dt>{escape(ui[key])} <code>({escape(key)})</code></dt><dd>{escape(description)}</dd>"
            for key, description in rule.criteria
        )
        cards.append(f"""<details><summary>{escape(axes[rule.id][0])}</summary><code>{escape(rule.id)}</code>
            <p>{escape(rule.instructions)}</p><dl>{options}</dl>
            <p>{escape(ui["thresholds"])}: P ≥ {rule.min_probability:.0%},
            confidence ≥ {rule.min_confidence:.0%}</p></details>""")
    method = ui["methodology"]
    routing_rule = report.get("routing_rule", "authorial_persuasion")
    return f"""<section class="legend methodology" id="methodology">
        <h2>{escape(method["title"])}</h2><p>{escape(method["intro"])}</p>
        <ol>{"".join(f"<li>{escape(step)}</li>" for step in method["steps"])}</ol>
        <p><b>{escape(method["scope_title"])}</b> {escape(method["scope"])}</p>
        <p>{escape(method["routing"])}: <code>{escape(routing_rule or method["no_routing"])}</code>.</p>
        <details><summary>{escape(method["exact"])}</summary>
        <p>{escape(method["exact_note"])}</p>{"".join(cards)}
        <details><summary>{escape(method["wire"])}</summary>
        <pre>{escape(json.dumps(questions, ensure_ascii=False, indent=2))}</pre></details>
        <p><a href="policy.json">policy.json</a> · <a href="questions.json">questions.json</a></p>
        </details><details><summary>{escape(method["adapt_title"])}</summary>
        <ol>{"".join(f"<li>{escape(step)}</li>" for step in method["adapt"])}</ol></details>
        </section>"""


def render_report(report: dict[str, Any], language: str) -> str:
    ui = load_json(ASSETS / f"ui.{language}.json")
    policy = Policy.from_dict(report["policy"])
    validate_news_policy(policy)
    routing_rule = report.get("routing_rule", "authorial_persuasion")
    if not report["bundled_samples"]:
        ui["title"] = ui["custom_title"]
        ui["intro"] = ui["custom_intro"]
    axes = feature_axes(policy.to_dict()["rules"], ui)
    other = "en" if language == "cz" else "cz"
    cards = []
    for article in report["articles"]:
        decision = article["decision"]
        checks = {c["id"]: c for c in decision["checks"]} if decision is not None else {}
        rows = []
        for rule in policy.rules:
            check = checks.get(rule.id)
            state = check["status"] if check else "not_measured"
            probabilities = dict(check["probabilities"]) if check else {}
            distribution = " · ".join(
                f"{ui[key]} {percent(probabilities.get(key), ui['unknown'])}"
                for key in ("present", "absent", "unclear")
            )
            confidence = percent(check["confidence"] if check else None, ui["unknown"])
            measurements = (
                f"<small>{escape(distribution)}</small>"
                f"<small>Confidence: {escape(confidence)}</small>"
                f"<small>{escape(ui['reason'])}: {escape(check['reason'])}</small>"
                if check
                else ""
            )
            rows.append(
                f"<tr><th>{escape(axes[rule.id][0])}</th>"
                f'<td><span class="badge {state}">{escape(ui[state])}</span>'
                f'<details class="metrics"><summary>{escape(ui["metrics"])}</summary>'
                f"{measurements}<small>{escape(ui['thresholds'])}: P ≥ {rule.min_probability:.0%}, "
                f"confidence ≥ {rule.min_confidence:.0%}</small></details></td></tr>"
            )
        cost = decision["cost"] if decision is not None else {}

        def amount(field: str, unit: str = "", values: dict[str, Any] = cost) -> str:
            value = values.get(field)
            return ui["unknown"] if value is None else escape(str(value)) + unit

        accounting = ""
        if decision is not None:
            accounting = f"""<div class="accounting">
                <p>{escape(ui["input"])}: <b>{amount("input_tokens")}</b> · {amount("input_usd", " USD")}</p>
                <p>{escape(ui["output"])}: <b>{amount("output_tokens")}</b> · {amount("output_usd", " USD")}</p>
                <p>{escape(ui["billed"])}: <b>{amount("billed_usd", " USD")}</b></p>
                <p>{escape(ui["calculated"])}: {amount("calculated_usd", " USD")}</p>
                <small>{escape(ui["price_note"])}</small>
                <small>{escape(str(cost.get("price_source") or ui["unknown"]))}</small>
                <small>{escape(str(cost.get("price_time") or ui["unknown"]))}</small>
                <small>{escape(str(decision.get("actual_model") or decision["requested_model"]))}</small>
                <small>{escape(str(decision.get("request_id") or ui["unknown"]))}</small>
            </div>"""
        error = (
            f'<p class="notice">{escape(decision["error"])}</p>'
            if decision is not None and decision["error"]
            else ""
        )
        paragraphs = "".join(
            f"<p>{escape(paragraph)}</p>" for paragraph in article["text"].split("\n\n")
        )
        name = article["id"].upper()
        cards.append(f"""<article class="card">
            <header><div class="eyebrow">{escape(ui["article"])} {name} · {article["words"]} {escape(ui["words"])}</div>
            <h2>{escape(article["text"].splitlines()[0])}</h2>
            <p class="route">{escape(ui[route(decision, policy, routing_rule)])}</p></header>
            <table>{"".join(rows)}</table>{error}{accounting}
            <details open><summary>{escape(ui["read_article"])}</summary>
            <div class="prose">{paragraphs}</div></details>
            <a class="download" href="article_{article["id"]}.txt">↓ TXT</a>
        </article>""")
    legend = "".join(
        f"<dt>{escape(title)}</dt><dd>{escape(description)}</dd>"
        for title, description in axes.values()
    )
    expected = ""
    translation_note = ""
    if report["bundled_samples"] and any(
        policy.fingerprint == Policy.from_dict(load_preset(language=lang)).fingerprint
        for lang in ("en", "cz")
    ):
        reference = load_json(ASSETS / "reference.json")
        columns = []
        for name in ("a", "b"):
            rows = "".join(
                f"<li><b>{escape(ui['axes'][key][0])}: {escape(ui[value])}</b><br>"
                f"<q>{escape(reference[name]['quotes'][report['text_language']][key])}</q></li>"
                for key, value in reference[name]["expected"].items()
            )
            columns.append(
                f"<div><h3>{escape(ui['article'])} {name.upper()}</h3><ul>{rows}</ul></div>"
            )
        expected = f"""<details class="reference"><summary>{escape(ui["reference_title"])}</summary>
            <p>{escape(ui["reference_note"])}</p><div class="grid">{"".join(columns)}</div></details>"""
        translation_note = f"""<details class="reference translation-note">
            <summary>{escape(ui["translation_title"])}</summary>
            <p>{escape(ui["translation_context"])}</p><p>{escape(ui["translation_limits"])}</p>
            </details>"""
    same = report["articles"][0]["sha256"] == report["articles"][1]["sha256"]
    identical = f'<p class="notice">{escape(ui["identical"])}</p>' if same else ""
    totals = []
    for field, label in (("billed_usd", "billed"), ("calculated_usd", "calculated")):
        total = report["costs"][field]
        totals.append(
            f"<span>{escape(ui[label])}: <b>{escape(total['known_sum'])} USD</b> "
            f"({escape(ui['unknown_calls'])}: {total['unknown_count']})</span>"
        )
    return f'''<!doctype html>
<html lang="{"cs" if language == "cz" else "en"}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>{escape(ui["title"])} · Sema Jev</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f1ec;color:#182c35;font:16px/1.65 system-ui,sans-serif}}
main{{max-width:1240px;margin:auto;padding:32px 28px 60px}}a{{color:#1d5c6c}}nav{{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}}
.hero{{padding:42px 0 28px;max-width:860px}}h1{{font-size:clamp(32px,5vw,58px);line-height:1.12;margin:18px 0}}h2{{font:600 28px/1.3 Georgia,serif;margin:12px 0;min-height:2.6em}}h3{{margin:0 0 10px}}
.eyebrow{{font-size:12px;letter-spacing:.13em;text-transform:uppercase;color:#49626d}}.mode{{background:#fff1d5;border:1px solid #d5b46a;padding:8px 13px;border-radius:8px;display:inline-block}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px;align-items:start}}.card{{background:#fff;border:1px solid #d6dce0;border-radius:12px;overflow:hidden}}
.card header{{padding:25px 25px 10px;border-top:5px solid #386b74}}.card:nth-child(2) header{{border-color:#94764b}}.route{{color:#53616a;font-size:14px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{text-align:left;padding:14px 20px;border-top:1px solid #e5e9eb;vertical-align:top}}th{{font-weight:500;width:44%}}
small{{display:block;color:#5c6a71;font-size:11px;overflow-wrap:anywhere;margin-top:5px}}.badge{{font-weight:600;border-radius:4px;padding:3px 7px;background:#edf0f1;color:#374f5b}}
.pass{{background:#dfedf2;color:#185269}}.review{{background:#fff0d5;color:#825716}}.not_measured{{background:#f0f0ee;color:#656763}}
details{{padding:20px 25px;border-top:1px solid #e5e9eb}}summary{{cursor:pointer;font-weight:600}}.prose{{font:17px/1.78 Georgia,serif;overflow-wrap:anywhere}}.prose p:first-child{{font-weight:bold}}
.metrics{{padding:5px 0 0;border:0;font-size:11px}}.metrics summary{{font-weight:400;color:#53616a}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;background:#f4f7f8;padding:16px}}.methodology h2{{min-height:0}}
.download{{display:inline-block;margin:0 25px 22px}}.legend,.reference{{background:#fff;border:1px solid #d6dce0;border-radius:12px;padding:25px;margin:24px 0}}
dl{{display:grid;grid-template-columns:240px 1fr;gap:12px 22px}}dt{{font-weight:600}}dd{{margin:0}}.reference li{{margin-bottom:15px}}q{{font-family:Georgia,serif}}.notice{{padding:15px;background:#fff0d5}}
.accounting{{padding:12px 22px;background:#f4f7f8;border-top:1px solid #e5e9eb;font-size:13px}}.accounting p{{margin:4px 0}}.totals{{display:flex;gap:20px;flex-wrap:wrap;font-size:13px;margin:16px 0 30px}}
footer{{font-size:13px;color:#566871}}@media(max-width:820px){{.grid{{grid-template-columns:1fr}}main{{padding:20px 14px}}dl{{grid-template-columns:1fr;gap:3px}}dd{{margin-bottom:13px}}}}
</style></head><body><main>
<nav><b>SEMA / NEWS LAB</b><div><a href="report.{other}.html">{"🇬🇧 English" if language == "cz" else "🇨🇿 Česky"}</a> · <a href="report.json">JSON</a></div></nav>
<section class="hero"><div class="mode">{escape(ui[report["mode"]])}</div>
<h1>{escape(ui["title"])}</h1><p>{escape(ui["intro"])}</p>
<p class="eyebrow">{escape(ui["text_language"])}: {report["text_language"].upper()} · {escape(ui["assessments"])}: {report["costs"]["assessments"]}</p></section>
{render_methodology(report, ui, policy)}
{identical}<div class="totals">{"".join(totals)}</div><div class="grid">{"".join(cards)}</div>
<section class="legend"><h2>{escape(ui["legend"])}</h2><dl>{legend}</dl>
<p>{escape(ui["threshold_note"])}</p><p>{escape(ui["limits"])}</p></section>{expected}{translation_note}
<footer>{escape(ui["footer"])}<br>Policy: {escape(policy.id)} / {escape(policy.version)} · {escape(policy.fingerprint)}</footer>
</main></body></html>'''


def validate_output(output: Path) -> Path:
    output = output.resolve()
    source = Path(__file__).resolve().parents[1]
    dev = (Path.home() / "dev").resolve()
    if output == dev or dev in output.parents or output == source:
        raise ValueError("Write reports outside source and ~/dev; use the dev-out runtime")
    if source in output.parents and source / "artifacts" not in (
        output,
        *output.parents,
    ):
        raise ValueError("Within the runtime, reports belong under artifacts/")
    return output


def save_report(report: dict[str, Any], output: Path) -> None:
    output = validate_output(output)
    output.mkdir(parents=True, exist_ok=True)
    for name in (
        "index.html",
        "report.json",
        "report.cz.html",
        "report.en.html",
        "article_a.txt",
        "article_b.txt",
        "policy.json",
        "questions.json",
    ):
        if (output / name).is_symlink():
            raise ValueError("Report files must not be symlinks")
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for article in report["articles"]:
        (output / f"article_{article['id']}.txt").write_text(article["text"], encoding="utf-8")
    policy = Policy.from_dict(report["policy"])
    for name, value in (
        ("policy", report["policy"]),
        (
            "questions",
            report.get("questions") or {r.id: r.question() for r in policy.rules},
        ),
    ):
        (output / f"{name}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    for language in ("en", "cz"):
        (output / f"report.{language}.html").write_text(
            render_report(report, language), encoding="utf-8"
        )

    (output / "index.html").write_text(render_report(report, "en"), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lang",
        choices=("en", "cz"),
        default="en",
        help="Article and default preset language",
    )
    parser.add_argument("--live", action="store_true", help="Make up to two billable Jev requests")
    parser.add_argument("--article-a", type=Path)
    parser.add_argument("--article-b", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--policy", type=Path, help="Override the language-specific default preset")
    parser.add_argument("--routing-rule", default="authorial_persuasion", help="Rule ID or 'none'")
    args = parser.parse_args(argv)
    policy = (
        Policy.load(args.policy)
        if args.policy
        else Policy.from_dict(load_preset(language=args.lang))
    )
    validate_news_policy(policy)
    routing_rule = None if args.routing_rule == "none" else args.routing_rule
    if routing_rule is not None and routing_rule not in {r.id for r in policy.rules}:
        parser.error("Unknown routing rule; use --routing-rule none for feature comparison")
    texts = tuple(
        (path or ASSETS / f"article_{name}.{args.lang}.txt").read_text(encoding="utf-8").strip()
        for name, path in (("a", args.article_a), ("b", args.article_b))
    )
    if any(not text for text in texts):
        parser.error("Both articles must be non-empty")
    output = (
        args.output or Path("artifacts") / f"news-{args.lang}-{'live' if args.live else 'preview'}"
    )
    output = validate_output(output)
    articles = prepare_articles((texts[0], texts[1]))
    if args.live:
        import os

        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            parser.error("OPENROUTER_API_KEY is missing. Use preview or configure it in dev-out.")
        evaluate_articles(articles, policy=policy)
    report = {
        "schema_version": 1,
        "mode": "live" if args.live else "preview",
        "text_language": args.lang,
        "bundled_samples": args.article_a is None and args.article_b is None,
        "policy": policy.to_dict(),
        "questions": {rule.id: rule.question() for rule in policy.rules},
        "routing_rule": routing_rule,
        "articles": articles,
        "costs": summarize_costs(articles),
    }
    save_report(report, output)
    print(f"{report['mode'].upper()}: {output.resolve() / 'index.html'}")
    print(f"{report['mode'].upper()}: {output.resolve() / 'report.cz.html'}")
    for article in articles:
        print(article["id"].upper(), route(article["decision"], policy, routing_rule))
    return (
        2
        if any(route(a["decision"], policy, routing_rule) == "review_queue" for a in articles)
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
