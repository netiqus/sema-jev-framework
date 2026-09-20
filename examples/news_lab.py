"""Local, server-rendered policy workbench. Keys never enter browser responses."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import threading
import uuid
from datetime import UTC, datetime
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from news_compare import (
    ASSETS,
    evaluate_articles,
    feature_axes,
    load_json,
    load_preset,
    prepare_articles,
    save_report,
    summarize_costs,
    validate_news_policy,
    validate_output,
)

from sema_jev import ConfigurationError, Policy
from sema_jev.providers import OpenRouter

MAX_BODY = 650_000
RUN_ID = re.compile(r"[a-f0-9]{32}")
DOWNLOADS = {
    "report.json",
    "policy.json",
    "questions.json",
    "index.html",
    "report.en.html",
    "report.cz.html",
    "article_a.txt",
    "article_b.txt",
}


def initial_draft(language: str) -> dict[str, Any]:
    return {
        "policy": load_preset(language=language),
        "articles": {
            name: (ASSETS / f"article_{name}.{language}.txt").read_text().strip()
            for name in ("a", "b")
        },
        "text_language": language,
        "routing_rule": "authorial_persuasion",
    }


def read_draft(fields: dict[str, str]) -> dict[str, Any]:
    count = int(fields.get("rule_count", "0"))
    if not 0 <= count <= 10:
        raise ConfigurationError("Use at most ten criteria")

    def number(key: str) -> float | str:
        value = fields.get(key, "")
        try:
            return float(value)
        except ValueError:
            return value

    rules = []
    for index in range(count):
        prefix = f"r{index}."
        rules.append(
            {
                "id": fields.get(prefix + "id", ""),
                "kind": "choice",
                "instructions": fields.get(prefix + "instructions", ""),
                "criteria": {
                    key: fields.get(prefix + key, "") for key in ("present", "absent", "unclear")
                },
                "accept": ["present"],
                "reject": ["absent"],
                "min_probability": number(prefix + "min_probability"),
                "min_confidence": number(prefix + "min_confidence"),
            }
        )
    return {
        "policy": {
            "schema_version": 1,
            "id": fields.get("policy_id", ""),
            "version": fields.get("policy_version", ""),
            "rules": rules,
            "required_fields": ["article"],
            "required_checks": [],
        },
        "articles": {name: fields.get("article_" + name, "").strip() for name in ("a", "b")},
        "text_language": fields.get("text_language", "other"),
        "routing_rule": fields.get("routing_rule") or None,
    }


def checked_policy(draft: dict[str, Any]) -> Policy:
    policy = Policy.from_dict(draft["policy"])
    validate_news_policy(policy)
    if draft["text_language"] not in ("en", "cz", "other"):
        raise ConfigurationError("Unknown article language")
    routing = draft["routing_rule"]
    if routing is not None and routing not in {r.id for r in policy.rules}:
        raise ConfigurationError("Select an existing routing rule or compare features only")
    questions = {r.id: r.question() for r in policy.rules}
    for text in draft["articles"].values():
        if not isinstance(text, str) or not text.strip():
            raise ConfigurationError("Both articles must be non-empty")
        payload = json.dumps(
            {"state": {"article": text}, "questions": questions},
            ensure_ascii=False,
            allow_nan=False,
        )
        if len(payload.encode()) > 500_000:
            raise ConfigurationError("Article and questions exceed the 500000-byte request limit")
    return policy


def field(
    name: str,
    label: str,
    value: Any,
    *,
    area: bool = False,
    rows: int = 3,
    kind: str = "text",
    extra: str = "",
) -> str:
    name, value = escape(name, quote=True), escape(str(value), quote=True)
    control = (
        f'<textarea name="{name}" rows="{rows}" {extra}>{value}</textarea>'
        if area
        else f'<input type="{kind}" name="{name}" value="{value}" {extra}>'
    )
    return f"<label>{escape(label)}{control}</label>"


def page(
    app: Workbench,
    draft: dict[str, Any],
    language: str,
    *,
    notice: str = "",
    inspect: bool = False,
    preset_language: str | None = None,
) -> str:
    preset_language = preset_language or language
    ui = load_json(ASSETS / f"lab.{language}.json")
    common = load_json(ASSETS / f"ui.{language}.json")
    method = common["methodology"]
    rule_cards = []
    policy = draft["policy"]
    axes = feature_axes(policy["rules"], common)
    for i, rule in enumerate(policy["rules"]):
        prefix = f"r{i}."
        definitions = "".join(
            field(prefix + key, ui[key], rule["criteria"].get(key, ""), area=True)
            for key in ("present", "absent", "unclear")
        )
        rule_cards.append(f"""<details class="criterion"><summary>{i + 1}. {escape(axes[rule["id"]][0] or ui["new_rule"])}</summary>
            {field(prefix + "id", ui["rule_id"], rule["id"])}
            {field(prefix + "instructions", ui["question"], rule["instructions"], area=True, rows=5)}
            <div class="definitions">{definitions}</div><div class="grid">
            {field(prefix + "min_probability", ui["probability"], rule["min_probability"], kind="number", extra='min="0.500001" max="1" step="any"')}
            {field(prefix + "min_confidence", ui["confidence"], rule["min_confidence"], kind="number", extra='min="0" max="1" step="any"')}</div>
            <button name="action" value="remove_{i}" formnovalidate>{escape(ui["remove"])}</button></details>""")
    options = f'<option value="">{escape(ui["no_routing"])}</option>'
    for rule in policy["rules"]:
        selected = " selected" if rule["id"] == draft["routing_rule"] else ""
        options += f'<option value="{escape(rule["id"], quote=True)}"{selected}>{escape(axes[rule["id"]][0])}</option>'
    languages = "".join(
        f'<option value="{code}"{" selected" if code == draft["text_language"] else ""}>{label}</option>'
        for code, label in (
            ("en", "English"),
            ("cz", "Čeština"),
            ("other", ui["other"]),
        )
    )
    raw = ""
    if inspect:
        selected_policy = checked_policy(draft)
        questions = {r.id: r.question() for r in selected_policy.rules}
        requests = [
            {
                "model": "typesafe/jev-1.13",
                "state": {"article": text},
                "questions": questions,
            }
            for text in draft["articles"].values()
        ]
        raw = f"""<section class="panel"><h2>{escape(ui["validated"])}</h2>
            <p>{escape(ui["fingerprint"])}: <code>{selected_policy.fingerprint}</code></p>
            <details open><summary>{escape(ui["questions"])}</summary><pre>{escape(json.dumps(questions, ensure_ascii=False, indent=2))}</pre></details>
            <details><summary>{escape(ui["requests"])}</summary><pre>{escape(json.dumps(requests, ensure_ascii=False, indent=2))}</pre></details></section>"""
    recent = []
    paths = sorted(app.root.glob("*/report.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in paths[:20]:
        if path.is_symlink() or path.parent.is_symlink() or not RUN_ID.fullmatch(path.parent.name):
            continue
        if not (path.parent / f"report.{language}.html").is_file():
            continue
        try:
            saved = load_json(path)
            label = f"{saved.get('created_at', '')} · {saved['policy']['id']} / {saved['policy']['version']} · {saved['text_language']}"
            recent.append(
                f'<li><a href="/runs/{path.parent.name}/report.{language}.html">{escape(label)}</a></li>'
            )
        except (OSError, ValueError, KeyError, TypeError):
            continue
    history = (
        f'<details class="panel"><summary>{escape(ui["history"])}</summary><ul>{"".join(recent)}</ul></details>'
        if recent
        else ""
    )
    key_state = ui["key_ready"] if app.key_available() else ui["key_missing"]
    return f'''<!doctype html><html lang="{"cs" if language == "cz" else "en"}"><head>
        <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
        <title>{escape(ui["title"])} · Sema Jev</title><style>
        *{{box-sizing:border-box}}body{{margin:0;background:#f3f1ec;color:#182c35;font:16px/1.6 system-ui,sans-serif}}
        main{{max-width:1200px;margin:auto;padding:28px}}a{{color:#1d5c6c}}h1{{font-size:42px;line-height:1.15}}h2{{font-size:25px}}
        .panel,.criterion{{background:white;border:1px solid #d6dce0;border-radius:10px;padding:22px;margin:20px 0}}
        .grid{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}.definitions{{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}}
        label{{display:block;font-weight:600;margin:12px 0}}input,textarea,select{{display:block;width:100%;padding:10px;margin-top:6px;border:1px solid #a9b7bc;border-radius:5px;background:white;color:#182c35;font:14px/1.5 system-ui}}
        textarea{{resize:vertical}}summary{{cursor:pointer;font-weight:700}}button{{cursor:pointer;padding:10px 15px;margin:5px 7px 5px 0;border:1px solid #7c939b;border-radius:6px;background:#fff;color:#182c35;font:600 14px system-ui}}
        .primary{{background:#235966;color:white}}.notice{{background:#fff0d5;padding:14px;border-radius:6px}}.muted{{font-size:13px;color:#52636b}}
        pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;background:#f1f5f6;padding:14px}}code{{overflow-wrap:anywhere}}
        nav,.actions{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}nav{{justify-content:space-between}}
        @media(max-width:780px){{main{{padding:16px}}.grid,.definitions{{grid-template-columns:1fr}}h1{{font-size:32px}}}}
        </style></head><body><main><form method="post" action="/">
        <input type="hidden" name="csrf" value="{app.csrf}">
        <input type="hidden" name="run_id" value="{uuid.uuid4().hex}">
        <input type="hidden" name="language" value="{language}">
        <input type="hidden" name="rule_count" value="{len(policy["rules"])}">
        <nav><b>SEMA / POLICY LAB</b><span>{escape(ui["interface"])}
        <button name="action" value="language_en" formnovalidate>English</button>
        <button name="action" value="language_cz" formnovalidate>Česky</button></span></nav>
        <h1>{escape(ui["title"])}</h1><p>{escape(ui["intro"])}</p>
        <p class="muted">OpenRouter · typesafe/jev-1.13 · {escape(key_state)}</p>
        {'<p class="notice" role="alert">' + escape(notice) + "</p>" if notice else ""}
        <section class="panel"><h2>{escape(method["title"])}</h2><p>{escape(method["intro"])}</p>
        <ol>{"".join(f"<li>{escape(step)}</li>" for step in method["steps"])}</ol>
        <p><b>{escape(method["scope_title"])}</b> {escape(method["scope"])}</p>
        <details><summary>{escape(method["adapt_title"])}</summary><ol>{"".join(f"<li>{escape(step)}</li>" for step in method["adapt"])}</ol></details></section>
        <section class="panel"><h2>{escape(ui["articles"])}</h2>
        <p>{escape(ui["article_note"])}</p>
        <button name="action" value="samples_en" formnovalidate>{escape(ui["samples_en"])}</button>
        <button name="action" value="samples_cz" formnovalidate>{escape(ui["samples_cz"])}</button>
        <label>{escape(common["text_language"])}<select name="text_language">{languages}</select></label>
        <div class="grid">{field("article_a", ui["article_a"], draft["articles"]["a"], area=True, rows=15)}
        {field("article_b", ui["article_b"], draft["articles"]["b"], area=True, rows=15)}</div></section>
        <section class="panel"><h2>{escape(ui["policy"])}</h2><p>{escape(ui["policy_note"])}</p>
        <label>{escape(ui["preset_language"])}<select name="preset_language">
        <option value="en"{" selected" if preset_language == "en" else ""}>English</option>
        <option value="cz"{" selected" if preset_language == "cz" else ""}>Čeština</option></select></label>
        <button name="action" value="preset_event" formnovalidate>{escape(ui["preset_event"])}</button>
        <button name="action" value="preset_general" formnovalidate>{escape(ui["preset_general"])}</button>
        <p class="muted">{escape(ui["preset_note"])}</p><div class="grid">
        {field("policy_id", ui["policy_id"], policy["id"])}{field("policy_version", ui["version"], policy["version"])}</div>
        {"".join(rule_cards)}<button name="action" value="add" formnovalidate>{escape(ui["add"])}</button>
        <p>{escape(ui["threshold_note"])}</p>
        <details><summary>{escape(ui["import_title"])}</summary>{field("policy_import", "JSON", "", area=True, rows=6)}
        <button name="action" value="import" formnovalidate>{escape(ui["import"])}</button></details></section>
        <section class="panel"><h2>{escape(ui["routing"])}</h2><p>{escape(ui["routing_note"])}</p>
        <label>{escape(ui["routing_question"])}<select name="routing_rule">{options}</select></label>
        <p class="muted">{escape(ui["routing_warning"])}</p></section>
        <section class="panel"><h2>{escape(ui["run"])}</h2><p>{escape(ui["paid_note"])}</p>
        <div class="actions"><button name="action" value="preview">{escape(ui["preview"])}</button>
        <button name="action" value="export">{escape(ui["export"])}</button>
        <button class="primary" name="action" value="evaluate" {"disabled" if not app.key_available() else ""}>{escape(ui["evaluate"])}</button></div>
        <p class="muted">{escape(ui["history_note"])}</p></section>{raw}
        </form>{history}<footer>{escape(ui["footer"])}</footer></main></body></html>'''


class Workbench:
    def __init__(self, root: Path, provider_factory: Any = OpenRouter) -> None:
        self.root = validate_output(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.csrf = secrets.token_urlsafe(32)
        self.provider_factory = provider_factory
        self.lock = threading.Lock()

    def key_available(self) -> bool:
        return bool(os.environ.get("OPENROUTER_API_KEY", "").strip())

    def run(self, run_id: str, draft: dict[str, Any]) -> Path:
        if not RUN_ID.fullmatch(run_id):
            raise ConfigurationError("Invalid run identifier; reload the editor")
        policy = checked_policy(draft)
        if not self.key_available():
            raise ConfigurationError("OPENROUTER_API_KEY is missing in the runtime")
        digest = hashlib.sha256(
            json.dumps(draft, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
        ).hexdigest()
        if not self.lock.acquire(blocking=False):
            raise ConfigurationError("Another assessment is running; wait for its result")
        try:
            output = self.root / run_id
            if output.exists():
                if output.is_symlink():
                    raise ConfigurationError("Invalid output path")
                previous = load_json(output / "submission.json")
                if previous["sha256"] == digest and (output / "report.json").is_file():
                    return output
                raise ConfigurationError(
                    "This submission was already used; open a new editor to retry"
                )
            output.mkdir(mode=0o700)
            # Persist the claim before the first paid request; a lost response must not trigger a retry.
            (output / "submission.json").write_text(json.dumps({"sha256": digest}))
            articles = prepare_articles(tuple(draft["articles"][name] for name in ("a", "b")))
            evaluate_articles(articles, self.provider_factory(), policy=policy)
            language = draft["text_language"]
            bundled = language in ("en", "cz") and all(
                a["text"] == (ASSETS / f"article_{a['id']}.{language}.txt").read_text().strip()
                for a in articles
            )
            report = {
                "schema_version": 1,
                "mode": "live",
                "text_language": language,
                "bundled_samples": bundled,
                "policy": policy.to_dict(),
                "questions": {r.id: r.question() for r in policy.rules},
                "routing_rule": draft["routing_rule"],
                "articles": articles,
                "created_at": datetime.now(UTC).isoformat(),
                "costs": summarize_costs(articles),
            }
            save_report(report, output)
            return output
        finally:
            self.lock.release()


def make_server(app: Workbench, port: int = 8770, language: str = "en") -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            pass  # Submitted articles and URLs are not access logs.

        def reply(
            self,
            status: int,
            body: str | bytes = "",
            content_type: str = "text/html; charset=utf-8",
            location: str | None = None,
            download: bool = False,
        ) -> None:
            raw = body.encode() if isinstance(body, str) else body
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'",
            )
            if location:
                self.send_header("Location", location)
            if download:
                self.send_header("Content-Disposition", 'attachment; filename="policy.json"')
            self.end_headers()
            self.wfile.write(raw)

        def allowed_host(self) -> bool:
            return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

        def do_GET(self) -> None:
            if not self.allowed_host():
                self.reply(403, "Invalid host")
                return
            parsed = urlsplit(self.path)
            params = parse_qs(parsed.query)
            lang = params.get("lang", [language])[0]
            lang = lang if lang in ("en", "cz") else language
            if parsed.path == "/":
                self.reply(200, page(app, initial_draft(lang), lang))
            elif parsed.path == "/edit":
                run_id = params.get("run", [""])[0]
                if not RUN_ID.fullmatch(run_id):
                    self.reply(404, "Not found")
                    return
                try:
                    report = load_json(app.root / run_id / "report.json")
                    draft = {
                        "policy": report["policy"],
                        "text_language": report["text_language"],
                        "routing_rule": report.get("routing_rule"),
                        "articles": {a["id"]: a["text"] for a in report["articles"]},
                    }
                    self.reply(200, page(app, draft, lang))
                except (OSError, ValueError):
                    self.reply(404, "Not found")
            else:
                match = re.fullmatch(r"/runs/([a-f0-9]{32})/([a-z_.]+)", parsed.path)
                if not match or match[2] not in DOWNLOADS:
                    self.reply(404, "Not found")
                    return
                path = app.root / match[1] / match[2]
                if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
                    self.reply(404, "Not found")
                    return
                content = path.read_bytes()
                if path.suffix == ".html":
                    lang = "cz" if match[2] == "report.cz.html" else "en"
                    ui = load_json(ASSETS / f"lab.{lang}.json")
                    link = f'<p><a href="/edit?run={match[1]}&amp;lang={lang}">{escape(ui["edit_run"])}</a></p>'
                    content = content.replace(b"<nav>", link.encode() + b"<nav>", 1)
                mime = {
                    ".json": "application/json",
                    ".txt": "text/plain",
                    ".html": "text/html",
                }[path.suffix]
                self.reply(200, content, mime + "; charset=utf-8")

        def do_POST(self) -> None:
            origin = f"http://127.0.0.1:{self.server.server_port}"
            if not self.allowed_host():
                self.reply(403, "Invalid host")
                return
            if self.headers.get("Origin") != origin:
                self.reply(403, "Invalid origin")
                return
            if (
                self.path != "/"
                or self.headers.get("Transfer-Encoding")
                or self.headers.get_content_type() != "application/x-www-form-urlencoded"
            ):
                self.reply(403, "Invalid request format")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BODY:
                    self.reply(413, "Request too large or empty")
                    return
                self.connection.settimeout(10)
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError("Incomplete request")
                values = parse_qs(raw.decode("utf-8"), keep_blank_values=True, max_num_fields=150)
                if any(len(v) != 1 for v in values.values()):
                    raise ValueError("Repeated form field")
                fields = {k: v[0] for k, v in values.items()}
                if not secrets.compare_digest(fields.get("csrf", ""), app.csrf):
                    self.reply(403, "Invalid session; reload the editor")
                    return
                lang = fields.get("language", language)
                if lang not in ("en", "cz"):
                    raise ValueError("Unknown interface language")
                preset_lang = fields.get("preset_language", lang)
                if preset_lang not in ("en", "cz"):
                    raise ValueError("Unknown preset language")
                draft = read_draft(fields)
            except (ValueError, OSError):
                self.reply(400, "Invalid form; reload the editor")
                return
            try:
                action = fields.get("action")
                if action == "evaluate":
                    output = app.run(fields.get("run_id", ""), draft)
                    self.reply(303, location=f"/runs/{output.name}/report.{lang}.html")
                    return
                if action in ("preview", "export"):
                    policy = checked_policy(draft)
                    if action == "export":
                        self.reply(
                            200,
                            json.dumps(policy.to_dict(), ensure_ascii=False, indent=2),
                            "application/json; charset=utf-8",
                            download=True,
                        )
                        return
                elif action in ("samples_en", "samples_cz"):
                    sample_lang = action.removeprefix("samples_")
                    sample = initial_draft(sample_lang)
                    draft.update(articles=sample["articles"], text_language=sample_lang)
                elif action in ("language_en", "language_cz"):
                    lang = action.removeprefix("language_")
                elif action in ("preset_event", "preset_general"):
                    draft["policy"] = load_preset(action.removeprefix("preset_"), preset_lang)
                    draft["routing_rule"] = (
                        "authorial_persuasion" if action == "preset_event" else None
                    )
                elif action == "import":
                    imported = Policy.from_dict(json.loads(fields.get("policy_import", "")))
                    validate_news_policy(imported)
                    draft["policy"] = imported.to_dict()
                    draft["routing_rule"] = None
                elif action == "add":
                    if len(draft["policy"]["rules"]) >= 10:
                        raise ConfigurationError("Use at most ten criteria")
                    existing_ids = {r["id"] for r in draft["policy"]["rules"]}
                    suffix = 1
                    while f"new_feature_{suffix}" in existing_ids:
                        suffix += 1
                    draft["policy"]["rules"].append(
                        {
                            "id": f"new_feature_{suffix}",
                            "kind": "choice",
                            "instructions": "",
                            "criteria": {"present": "", "absent": "", "unclear": ""},
                            "accept": ["present"],
                            "reject": ["absent"],
                            "min_probability": 0.85,
                            "min_confidence": 0.6,
                        }
                    )
                elif action and re.fullmatch(r"remove_[0-9]", action):
                    draft["policy"]["rules"].pop(int(action[-1]))
                    if draft["routing_rule"] not in {r["id"] for r in draft["policy"]["rules"]}:
                        draft["routing_rule"] = None
                else:
                    raise ConfigurationError("Unknown action")
                self.reply(
                    200,
                    page(
                        app,
                        draft,
                        lang,
                        inspect=action == "preview",
                        preset_language=preset_lang,
                    ),
                )
            except ConfigurationError as exc:
                ui = load_json(ASSETS / f"lab.{lang}.json")
                self.reply(
                    400,
                    page(
                        app,
                        draft,
                        lang,
                        notice=ui["invalid_prefix"] + str(exc),
                        preset_language=preset_lang,
                    ),
                )
            except (ValueError, TypeError, KeyError, IndexError):
                ui = load_json(ASSETS / f"lab.{lang}.json")
                self.reply(
                    400,
                    page(
                        app,
                        draft,
                        lang,
                        notice=ui["invalid"],
                        preset_language=preset_lang,
                    ),
                )
            except Exception:
                # Never echo transport errors, submitted text, or credentials into HTML/logs.
                self.reply(
                    500,
                    "Run stopped. No automatic retry. Inspect the saved run before resubmitting.",
                )

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--lang", choices=("en", "cz"), default="en")
    parser.add_argument("--output", type=Path, default=Path("artifacts/news-lab/runs"))
    args = parser.parse_args()
    app = Workbench(args.output)
    server = make_server(app, args.port, args.lang)
    print(
        f"News policy lab: http://127.0.0.1:{server.server_port}/?lang={args.lang}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
