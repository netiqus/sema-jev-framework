"""Verify the installed distribution and CLI outside the source checkout."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

wheel = next(Path(sys.argv[1]).resolve().glob("*.whl"))
env = {
    key: value
    for key, value in os.environ.items()
    if key not in ("OPENROUTER_API_KEY", "TYPESAFE_API_KEY", "PYTHONPATH")
}
with tempfile.TemporaryDirectory(
    prefix="sema-wheel-", dir=Path(sys.argv[1]).resolve().parent
) as path:
    root = Path(path)
    subprocess.run(["uv", "venv", "--python", sys.executable, str(root / "venv")], check=True)
    bin_dir = root / "venv" / ("Scripts" if os.name == "nt" else "bin")
    python = bin_dir / ("python.exe" if os.name == "nt" else "python")
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), "--no-deps", "--offline", str(wheel)],
        check=True,
        cwd=root,
        env=env,
    )
    code = """
from importlib.metadata import version
from sema_jev import FakeProvider, Gate, Policy, Rule, __version__

assert version("sema-jev-framework") == __version__
for option, expected in (("supported", "pass"), ("contradicted", "fail"), ("insufficient", "review")):
    probabilities = dict.fromkeys(("supported", "contradicted", "insufficient"), 0.01)
    probabilities[option] = 0.98
    provider = FakeProvider({"requirement": {"type": "choice", "choice": option,
        "probabilities": probabilities, "confidence": 0.95}})
    result = Gate("Does the message request a refund?", provider=provider).check("synthetic")
    assert result.status == expected
    assert result.passed == (expected == "pass")
    assert provider.calls == 1
policy = Policy("installation", (Rule.require("request", "Does the message request a refund?"),))
policy_path = __import__("pathlib").Path("policy.json")
policy_path.write_text(__import__("json").dumps(policy.to_dict()))
print("Installed wheel: pass/fail/review and package version verified offline")
"""
    subprocess.run([str(python), "-I", "-c", code], check=True, cwd=root, env=env)
    executable = bin_dir / ("sema-jev.exe" if os.name == "nt" else "sema-jev")
    for command in ([str(executable)], [str(python), "-I", "-m", "sema_jev.cli"]):
        result = subprocess.run(
            [*command, "policy.json"],
            input='{"state":{"message":"synthetic"}}',
            text=True,
            capture_output=True,
            cwd=root,
            env=env,
        )
        assert result.returncode == 2, "Missing key must produce review"
        decision = json.loads(result.stdout)
        assert decision["status"] == "review" and decision["error"] == "missing_api_key"
        assert decision["cost"]["input_tokens"] is None
    print("Installed CLI: executable and module entry points verified without a key")
