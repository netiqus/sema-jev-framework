import copy
import json
import runpy
from pathlib import Path

import pytest

from sema_jev import FakeProvider, Policy


@pytest.fixture
def news():
    return runpy.run_path("examples/news_compare.py")


def fixture_answers(expected):
    answers = {}
    for name, value in expected.items():
        probabilities = dict.fromkeys(("present", "absent", "unclear"), 0.01)
        probabilities[value] = 0.98
        answers[name] = {
            "type": "choice",
            "choice": value,
            "confidence": 0.95,
            "probabilities": probabilities,
        }
    return answers


@pytest.mark.parametrize("language", ["en", "cz"])
def test_independent_inputs_and_opinion_routing(news, language):
    reference = json.loads(Path("examples/news/reference.json").read_text(encoding="utf-8"))
    texts = tuple(
        Path(f"examples/news/article_{name}.{language}.txt").read_text(encoding="utf-8")
        for name in ("a", "b")
    )

    class CapturingProvider(FakeProvider):
        def __init__(self):
            super().__init__([fixture_answers(reference[n]["expected"]) for n in ("a", "b")])
            self.requests = []

        def evaluate(self, state, questions):
            self.requests.append(copy.deepcopy((state, questions)))
            return super().evaluate(state, questions)

    provider = CapturingProvider()
    articles = news["prepare_articles"](texts)
    news["evaluate_articles"](articles, provider)
    assert [request[0] for request in provider.requests] == [{"article": text} for text in texts]
    assert provider.requests[0][1] == provider.requests[1][1]
    assert provider.calls == 2
    # Different feature profiles must not be mistaken for article rejection.
    assert all(article["decision"]["status"] == "fail" for article in articles)
    assert [news["route"](a["decision"]) for a in articles] == ["commentary_queue"] * 2


def test_uncertainty_and_provider_failure_stay_observable(news):
    policy = Policy.load("examples/news/policy.json")
    expected = dict.fromkeys((rule.id for rule in policy.rules), "absent")
    articles = news["prepare_articles"](("first", "second"))
    uncertain = fixture_answers({**expected, "rights_and_oversight": "unclear"})
    provider = FakeProvider([uncertain, fixture_answers(expected)])
    news["evaluate_articles"](articles, provider)
    assert news["route"](articles[0]["decision"]) == "review_queue"
    assert news["route"](articles[1]["decision"]) == "reporting_queue"
    articles = news["prepare_articles"](("first", "second"))
    provider = FakeProvider({"unexpected": {}})
    news["evaluate_articles"](articles, provider)
    assert provider.calls == 1
    assert articles[0]["decision"]["error"] == "invalid_response"
    assert news["route"](articles[0]["decision"]) == "review_queue"
    assert articles[1]["decision"] is None


def test_unknown_cost_is_not_a_free_request(news):
    articles = [
        {"decision": {"cost": {"billed_usd": "0.002", "calculated_usd": None}}},
        {"decision": {"cost": {"billed_usd": None, "calculated_usd": "0"}}},
        {"decision": None},
    ]
    totals = news["summarize_costs"](articles)
    assert totals["assessments"] == 2
    assert totals["billed_usd"] == {"known_sum": "0.002", "unknown_count": 1}
    assert totals["calculated_usd"] == {"known_sum": "0", "unknown_count": 1}


@pytest.mark.parametrize("language", ["en", "cz"])
def test_preview_does_not_measure_or_leak_html(news, tmp_path, language):
    malicious = "A <script>alert(1)</script> & another paragraph"
    article = tmp_path / "custom.txt"
    article.write_text(malicious, encoding="utf-8")
    output = tmp_path / "report"
    assert (
        news["main"](
            [
                "--lang",
                language,
                "--article-a",
                str(article),
                "--article-b",
                str(article),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    saved = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert saved["mode"] == "preview"
    preset = json.loads(Path(f"examples/news/policy.{language}.json").read_text())
    assert saved["policy"] == Policy.from_dict(preset).to_dict()
    assert saved["costs"]["assessments"] == 0
    assert all(a["decision"] is None for a in saved["articles"])
    for ui_language in ("cz", "en"):
        html = (output / f"report.{ui_language}.html").read_text(encoding="utf-8")
        assert "<script>" not in html and "&lt;script&gt;" in html
        assert '<details class="reference">' not in html
        assert f"report.{'cz' if ui_language == 'en' else 'en'}.html" in html
    assert saved["articles"][0]["sha256"] == saved["articles"][1]["sha256"]


def test_bundled_references_are_exact_excerpts(news):
    reference = json.loads(Path("examples/news/reference.json").read_text(encoding="utf-8"))
    for name in ("a", "b"):
        for language in ("cz", "en"):
            text = Path(f"examples/news/article_{name}.{language}.txt").read_text(encoding="utf-8")
            for quote in reference[name]["quotes"][language].values():
                assert quote in text
    article = news["prepare_articles"]((text, text))
    report = {
        "articles": article,
        "text_language": "en",
        "bundled_samples": True,
        "costs": news["summarize_costs"](article),
        "mode": "preview",
        "policy": Policy.load("examples/news/policy.json").to_dict(),
    }
    assert '<details class="reference">' in news["render_report"](report, "en")


def test_live_requires_runtime_key_and_source_rejects_outputs(news, monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    output = tmp_path / "missing-key"
    with pytest.raises(SystemExit) as error:
        news["main"](["--live", "--output", str(output)])
    assert error.value.code == 2 and not output.exists()
    with pytest.raises(ValueError):
        news["save_report"]({}, Path.home() / "dev/sema-jev-framework/artifacts/forbidden")
