import copy
import http.client
import importlib
import json
import threading
import uuid
from html import unescape
from pathlib import Path
from urllib.parse import urlencode

import pytest

from sema_jev import ConfigurationError, FakeProvider, Policy


@pytest.fixture
def lab(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("examples").resolve()))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret-not-for-html")
    return importlib.import_module("news_lab")


def answers(policy, choice="present", confidence=0.95):
    return {
        rule["id"]: {
            "type": "choice",
            "choice": choice,
            "confidence": confidence,
            "probabilities": {
                key: 0.98 if key == choice else 0.01 for key in ("present", "absent", "unclear")
            },
        }
        for rule in policy["rules"]
    }


class RecordingProvider(FakeProvider):
    def __init__(self, values):
        super().__init__(values)
        self.requests = []

    def evaluate(self, state, questions):
        self.requests.append(copy.deepcopy({"state": state, "questions": questions}))
        return super().evaluate(state, questions)


def form(app, draft, action="preview", run_id=None):
    result = {
        "csrf": app.csrf,
        "run_id": run_id or uuid.uuid4().hex,
        "action": action,
        "language": "cz",
        "text_language": draft["text_language"],
        "article_a": draft["articles"]["a"],
        "article_b": draft["articles"]["b"],
        "policy_id": draft["policy"]["id"],
        "policy_version": draft["policy"]["version"],
        "routing_rule": draft["routing_rule"] or "",
        "rule_count": str(len(draft["policy"]["rules"])),
    }
    for i, rule in enumerate(draft["policy"]["rules"]):
        for key in ("id", "instructions", "min_probability", "min_confidence"):
            result[f"r{i}.{key}"] = str(rule[key])
        for key, value in rule["criteria"].items():
            result[f"r{i}.{key}"] = value
    return result


def test_edited_questions_snapshot_routing_and_duplicate_submission(lab, tmp_path):
    draft = lab.initial_draft("cz")
    draft["articles"] = {"a": "First original", "b": "Second original"}
    draft["policy"]["rules"] = draft["policy"]["rules"][:1]
    rule = draft["policy"]["rules"][0]
    rule.update(
        id="authorial_tone",
        instructions="Does `article` praise product X?",
        min_confidence=0.96,
    )
    rule["criteria"]["present"] = "The author praises X, not merely a quote."
    draft["routing_rule"] = None
    provider = RecordingProvider([answers(draft["policy"])] * 2)
    app = lab.Workbench(tmp_path / "runs", lambda: provider)
    run_id = uuid.uuid4().hex
    output = app.run(run_id, draft)
    report = json.loads((output / "report.json").read_text())
    assert provider.calls == 2
    assert [r["state"] for r in provider.requests] == [
        {"article": "First original"},
        {"article": "Second original"},
    ]
    assert all(r["questions"] == report["questions"] for r in provider.requests)
    assert all(
        r["questions"]["authorial_tone"]["criteria"] == rule["criteria"] for r in provider.requests
    )
    assert (
        "Does `article` praise product X?" in report["questions"]["authorial_tone"]["instructions"]
    )
    assert report["articles"][0]["decision"]["checks"][0]["status"] == "review"
    saved = (output / "report.json").read_bytes()
    assert app.run(run_id, draft) == output
    assert provider.calls == 2 and (output / "report.json").read_bytes() == saved
    changed = copy.deepcopy(draft)
    changed["articles"]["a"] = "Different evidence"
    with pytest.raises(ConfigurationError, match="already used"):
        app.run(run_id, changed)
    assert provider.calls == 2
    # The saved rendering must never pull a newly edited policy from the source assets.
    compare = importlib.import_module("news_compare")
    html = compare.render_report(report, "cz")
    assert "authorial_tone" in html and "P ≥ 85%" in html and "confidence ≥ 96%" in html
    assert "Does `article` praise product X?" in html
    assert "Autorský klíč — otevřít" not in html
    assert (
        compare.route(report["articles"][0]["decision"], Policy.from_dict(report["policy"]), None)
        == "review_queue"
    )
    assert all("test-secret-not-for-html" not in p.read_text() for p in output.iterdir())


def test_bad_inputs_never_reach_provider_and_unknown_failure_is_not_retried(lab, tmp_path):
    draft = lab.initial_draft("en")
    provider = RecordingProvider([answers(draft["policy"])] * 2)
    app = lab.Workbench(tmp_path / "runs", lambda: provider)
    for change in ("blank", "threshold", "routing", "options"):
        bad = copy.deepcopy(draft)
        if change == "blank":
            bad["articles"]["a"] = " "
        elif change == "threshold":
            bad["policy"]["rules"][0]["min_probability"] = 0.5
        elif change == "routing":
            bad["routing_rule"] = "missing"
        else:
            bad["policy"]["rules"][0]["criteria"]["surprise"] = "Extra response"
        with pytest.raises(ConfigurationError):
            app.run(uuid.uuid4().hex, bad)
    assert provider.calls == 0

    class Broken:
        calls = 0

        def evaluate(self, state, questions):
            self.calls += 1
            raise RuntimeError("A lost response might have been billable")

    broken = Broken()
    app.provider_factory = lambda: broken
    run_id = uuid.uuid4().hex
    with pytest.raises(RuntimeError):
        app.run(run_id, draft)
    with pytest.raises(ConfigurationError, match="already used"):
        app.run(run_id, draft)
    assert broken.calls == 1


def test_provider_error_stops_second_article(lab, tmp_path):
    draft = lab.initial_draft("en")
    provider = RecordingProvider({"unexpected": {}})
    output = lab.Workbench(tmp_path / "runs", lambda: provider).run(uuid.uuid4().hex, draft)
    report = json.loads((output / "report.json").read_text())
    assert provider.calls == 1
    assert report["articles"][0]["decision"]["error"] == "invalid_response"
    assert report["articles"][1]["decision"] is None


@pytest.fixture
def web(lab, tmp_path):
    draft = lab.initial_draft("cz")
    provider = RecordingProvider([answers(draft["policy"])] * 2)
    app = lab.Workbench(tmp_path / "runs", lambda: provider)
    server = lab.make_server(app, 0, "cz")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(method, path="/", fields=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        body = urlencode(fields).encode() if fields is not None else None
        options = {
            "Origin": f"http://127.0.0.1:{server.server_port}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        options.update(headers or {})
        connection.request(method, path, body, options)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read().decode()
        connection.close()
        return result

    yield app, draft, provider, request
    server.shutdown()
    server.server_close()
    thread.join()


def test_http_form_inspection_export_and_saved_run(web):
    app, draft, provider, request = web
    status, headers, html = request("GET")
    assert status == 200 and "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "Přesné zadání pro posouzení" in html
    assert "test-secret-not-for-html" not in html
    fields = form(app, draft)
    fields["article_a"] = '</textarea><script>alert("x")</script>'
    status, _, html = request("POST", fields=fields)
    assert status == 200 and "&lt;script&gt;" in html and "<script>" not in html
    assert "API nebylo voláno" in html and provider.calls == 0
    status, headers, body = request("POST", fields=form(app, draft, "export"))
    assert status == 200 and "attachment" in headers["Content-Disposition"]
    assert (
        Policy.from_dict(json.loads(body)).fingerprint
        == Policy.from_dict(draft["policy"]).fingerprint
    )
    fields = form(app, draft, "evaluate")
    status, headers, _ = request("POST", fields=fields)
    assert status == 303
    location = headers["Location"]
    assert request("POST", fields=fields)[1]["Location"] == location and provider.calls == 2
    status, _, html = request("GET", location)
    assert (
        status == 200
        and "Upravit tyto texty" in html
        and "Jak jsme toto hodnocení sestavili" in html
    )
    assert request("GET", location.replace("report.cz.html", "policy.json"))[0] == 200
    run_id = location.split("/")[2]
    status, _, html = request("GET", f"/edit?run={run_id}&lang=cz")
    assert status == 200 and draft["policy"]["rules"][0]["instructions"] in unescape(html)


@pytest.mark.parametrize("mutation", ["origin", "null_origin", "host", "csrf", "duplicate", "size"])
def test_http_rejects_untrusted_or_malformed_paid_requests(web, mutation):
    app, draft, provider, request = web
    fields, headers = form(app, draft, "evaluate"), {}
    if mutation == "origin":
        headers["Origin"] = "https://untrusted.invalid"
    elif mutation == "null_origin":
        headers["Origin"] = "null"
    elif mutation == "host":
        headers["Host"] = "untrusted.invalid"
    elif mutation == "csrf":
        fields["csrf"] = "wrong"
    elif mutation == "duplicate":
        fields = list(fields.items()) + [("action", "evaluate")]
    else:
        headers["Content-Length"] = "650001"
    status, _, _ = request("POST", fields=fields, headers=headers)
    assert status in (400, 403, 413)
    assert provider.calls == 0
    assert request("GET", "/config/runtime.env")[0] == 404


def test_general_preset_is_exportable_and_has_no_automatic_routing(lab, web):
    app, draft, provider, request = web
    status, _, html = request("POST", fields=form(app, draft, "preset_general"))
    assert status == 200 and "visible-rhetoric-experimental" in html
    general = lab.load_preset("general", "cz")
    assert general["rules"][0]["instructions"] in unescape(html)
    lab.validate_news_policy(Policy.from_dict(general))
    assert not {"welcomes_visit", "rights_and_oversight", "leader_over_scrutiny"} & {
        r["id"] for r in general["rules"]
    }
    assert provider.calls == 0


@pytest.mark.parametrize("preset", ["event", "general"])
@pytest.mark.parametrize("language", ["cz", "en"])
def test_localized_presets_reach_provider_and_saved_report(lab, web, preset, language):
    app, draft, provider, request = web
    policy = lab.load_preset(preset, language)
    fields = form(app, draft, f"preset_{preset}")
    fields["preset_language"] = language
    status, _, html = request("POST", fields=fields)
    assert status == 200
    for rule in policy["rules"]:
        assert rule["instructions"] in unescape(html)
        assert all(definition in unescape(html) for definition in rule["criteria"].values())
    assert '<option value="' + language + '" selected>' in html
    assert provider.calls == 0
    # Capture the real Gate input and retain it verbatim in both report languages.
    draft.update(policy=policy, routing_rule=None)
    recording = RecordingProvider([answers(policy)] * 2)
    app.provider_factory = lambda: recording
    status, headers, _ = request("POST", fields=form(app, draft, "evaluate"))
    assert status == 303 and recording.calls == 2
    for sent in recording.requests:
        for rule in policy["rules"]:
            assert rule["instructions"] in sent["questions"][rule["id"]]["instructions"]
            assert sent["questions"][rule["id"]]["criteria"] == rule["criteria"]
    for report_language in ("cz", "en"):
        location = headers["Location"].replace("report.cz", f"report.{report_language}")
        status, _, html = request("GET", location)
        assert status == 200 and policy["rules"][0]["instructions"] in unescape(html)


def test_interface_language_preserves_custom_draft_and_historical_questions(lab, web):
    app, draft, provider, request = web
    english = lab.initial_draft("en")
    status, headers, _ = request("POST", fields=form(app, english, "evaluate"))
    assert status == 303
    run_id = headers["Location"].split("/")[2]
    saved = (app.root / run_id / "report.json").read_bytes()
    status, _, html = request("GET", f"/edit?run={run_id}&lang=cz")
    assert status == 200 and english["policy"]["rules"][0]["instructions"] in unescape(html)
    draft["policy"]["rules"][0]["instructions"] = "Moje vlastní česká otázka o výrobku."
    draft["articles"]["a"] = "Vlastní podklad s diakritikou."
    fields = form(app, draft, "language_en")
    fields["preset_language"] = "cz"
    status, _, html = request("POST", fields=fields)
    assert status == 200 and '<html lang="en">' in html
    assert draft["policy"]["rules"][0]["instructions"] in html
    assert draft["articles"]["a"] in html
    assert '<option value="cz" selected>' in html
    assert (app.root / run_id / "report.json").read_bytes() == saved
    assert provider.calls == 2
