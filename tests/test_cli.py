import io
import json
import sys

import pytest

from sema_jev import FakeProvider, Gate, Policy, Rule, cli


@pytest.mark.parametrize(
    "option,code", [("supported", 0), ("contradicted", 1), ("insufficient", 2)]
)
def test_cli_status_contract(monkeypatch, capsys, tmp_path, option, code):
    policy = Policy("cli", (Rule.require("r", "Does it meet the requirement?"),))
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy.to_dict()))
    probabilities = dict.fromkeys(("supported", "contradicted", "insufficient"), 0.01)
    probabilities[option] = 0.98
    fake = FakeProvider(
        {
            "r": {
                "type": "choice",
                "choice": option,
                "probabilities": probabilities,
                "confidence": 0.95,
            }
        }
    )
    monkeypatch.setattr(cli, "Gate", lambda p, **kw: Gate(p, provider=fake))
    monkeypatch.setattr(sys, "argv", ["sema-jev", str(path)])
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b'{"state":"test"}')))
    assert cli.main() == code
    assert (
        json.loads(capsys.readouterr().out)["status"] == {0: "pass", 1: "fail", 2: "review"}[code]
    )


@pytest.mark.parametrize("payload", [b"bad", b'{"state":"x","unexpected":true}', b"x" * 500001])
def test_cli_rejects_bad_input(monkeypatch, capsys, payload):
    monkeypatch.setattr(sys, "argv", ["sema-jev", "unused.json"])
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(payload)))
    assert cli.main() == 3
    captured = capsys.readouterr()
    assert not captured.out
    assert json.loads(captured.err)["error"] == "invalid_configuration_or_input"


def test_cli_missing_key_is_review(monkeypatch, capsys, tmp_path):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(Policy("cli", (Rule.require("r", "Met?"),)).to_dict()))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["sema-jev", str(path)])
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b'{"state":"test"}')))
    assert cli.main() == 2
    assert json.loads(capsys.readouterr().out)["error"] == "missing_api_key"
