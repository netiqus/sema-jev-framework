"""Mirror approved source files to a separate runtime before executing tools."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent
SOURCE_FILES = (
    "dev.sh",
    "pyproject.toml",
    "uv.lock",
    "LICENSE",
    "README.md",
    "README.cz.md",
    "README.en.md",
    "CHANGELOG.md",
    "CHANGELOG.cz.md",
    "CHANGELOG.en.md",
    "CONTRIBUTING.md",
    "CONTRIBUTING.en.md",
    "CONTRIBUTING.cz.md",
)
SOURCE_DIRS = ("src", "tests", "examples", "policies", "evals", "scripts", "docs")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all generated work outside the source tree")
    parser.add_argument(
        "action",
        choices=(
            "sync",
            "lint",
            "types",
            "test",
            "check",
            "build",
            "demo",
            "news",
            "news-live",
            "news-lab",
            "live",
            "evaluate",
            "export",
        ),
    )
    parser.add_argument("--python", default="3.11", help="Python version for the isolated runtime")
    parser.add_argument("--lang", choices=("en", "cz"), default="en", help="News article language")
    parser.add_argument("--port", type=int, default=8770, help="Local news editor port")
    parser.add_argument("--export-dir", type=Path, help="New directory for a public source export")
    args = parser.parse_args()
    if os.environ.get("SEMA_OUT_DIR"):
        runtime = Path(os.environ["SEMA_OUT_DIR"]).expanduser().resolve()
    else:
        try:
            relative = SOURCE.relative_to(Path.home() / "dev")
            runtime = (Path.home() / "dev-out" / relative).resolve()
        except ValueError:
            runtime = (SOURCE.parent / (SOURCE.name + "-out")).resolve()
    dev_root = (Path.home() / "dev").resolve()
    if (
        runtime == SOURCE
        or SOURCE in runtime.parents
        or runtime == dev_root
        or dev_root in runtime.parents
        or runtime in SOURCE.parents
    ):
        parser.error("Runtime must be separate from source and outside ~/dev")
    subprocess.run(
        [sys.executable, "-B", str(SOURCE / "scripts/check_source.py"), str(SOURCE)], check=True
    )
    runtime.mkdir(parents=True, exist_ok=True)
    for name in SOURCE_FILES:
        if (SOURCE / name).is_file():
            shutil.copy2(SOURCE / name, runtime / name)
    for name in SOURCE_DIRS:
        destination = runtime / name
        if destination.is_symlink():
            parser.error("Runtime source directory must not be a symlink")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(SOURCE / name, destination)
    env = os.environ.copy()
    env.update(
        UV_PROJECT_ENVIRONMENT=str(runtime / ".venv"),
        UV_CACHE_DIR=str(runtime / "cache/uv"),
        PYTHONPYCACHEPREFIX=str(runtime / "cache/pycache"),
        MYPY_CACHE_DIR=str(runtime / "cache/mypy"),
        RUFF_CACHE_DIR=str(runtime / "cache/ruff"),
        COVERAGE_FILE=str(runtime / "artifacts/.coverage"),
    )
    (runtime / "artifacts").mkdir(exist_ok=True)
    (runtime / "config").mkdir(exist_ok=True, mode=0o700)
    # Config loading is explicit and restricted to the local runtime.
    config = runtime / "config/runtime.env"
    if config.exists():
        import shlex

        if os.name != "nt" and config.stat().st_mode & 0o077:
            parser.error("Runtime config must have permissions 0600")
        for line in config.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, _, value = line.partition("=")
            if key not in ("OPENROUTER_API_KEY", "TYPESAFE_API_KEY"):
                parser.error("Unknown runtime config key")
            parts = shlex.split(value)
            if len(parts) > 1:
                parser.error("Invalid runtime config value")
            env.setdefault(key, parts[0] if parts else "")
    print(f"Runtime: {runtime}", flush=True)

    def run(*command: str) -> None:
        subprocess.run(command, cwd=runtime, env=env, check=True)

    sync = ["uv", "sync", "--python", args.python]
    if (runtime / "uv.lock").exists():
        sync.append("--locked")
    run(*sync)
    if not (SOURCE / "uv.lock").exists():
        # A dependency lock is source metadata, never credentials/runtime config.
        shutil.copy2(runtime / "uv.lock", SOURCE / "uv.lock")
    python = str(runtime / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))
    if args.action in ("lint", "check"):
        targets = ("src", "tests", "examples", "evals", "scripts")
        run(python, "-m", "ruff", "check", *targets)
        run(python, "-m", "ruff", "format", "--check", *targets)
        run(python, "scripts/check_docs.py")
    if args.action in ("types", "check"):
        run(python, "-m", "mypy")
    if args.action in ("test", "check"):
        run(
            python,
            "-m",
            "pytest",
            "--cov=sema_jev",
            "--cov-report=term-missing",
            "-o",
            "cache_dir=cache/pytest",
        )
    if args.action in ("build", "check"):
        distribution = runtime / "artifacts/dist"
        if distribution.is_symlink():
            parser.error("Distribution output must not be a symlink")
        distribution.mkdir(exist_ok=True)
        for artifact in list(distribution.glob("*.whl")) + list(distribution.glob("*.tar.gz")):
            artifact.unlink()
        run(python, "-m", "build", "--outdir", "artifacts/dist")
        run(python, "scripts/check_artifacts.py", "artifacts/dist")
        run(
            python,
            "-m",
            "twine",
            "check",
            *[str(p) for p in (runtime / "artifacts/dist").glob("*")],
        )
        run(python, "scripts/wheel_smoke.py", "artifacts/dist")
    if args.action == "demo":
        run(python, "examples/offline.py")
    if args.action in ("news", "news-live"):
        options = ["--lang", args.lang]
        if args.action == "news-live":
            options.append("--live")
        run(python, "examples/news_compare.py", *options)
    if args.action == "news-lab":
        run(python, "examples/news_lab.py", "--lang", args.lang, "--port", str(args.port))
    if args.action == "live":
        run(python, "examples/live.py")
    if args.action == "evaluate":
        run(python, "evals/run.py", "--live", "--output", "artifacts/evaluation.json")
    if args.action == "export":
        run(
            python,
            "scripts/public_export.py",
            str(SOURCE),
            str(
                args.export_dir.resolve()
                if args.export_dir
                else runtime / "artifacts/public-source"
            ),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
