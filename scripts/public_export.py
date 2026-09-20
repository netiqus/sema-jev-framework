"""Create an inspected source snapshot with explicitly selected public workflows."""

from __future__ import annotations

import argparse
import runpy
import shutil
from pathlib import Path

PUBLIC_DIRS = ("src", "tests", "examples", "policies", "evals", "scripts", "docs")
PUBLIC_FILES = (
    "LICENSE",
    "README.md",
    "README.en.md",
    "README.cz.md",
    "CHANGELOG.md",
    "CHANGELOG.en.md",
    "CHANGELOG.cz.md",
    "CONTRIBUTING.md",
    "CONTRIBUTING.en.md",
    "CONTRIBUTING.cz.md",
    "pyproject.toml",
    "uv.lock",
    "dev.sh",
    ".gitignore",
)
PUBLIC_WORKFLOWS = ("ci.yml", "release.yml", "live-evaluation.yml")
ALLOWED_SUFFIXES = {".py", ".typed", ".md", ".json", ".txt", ".example"}


def export_source(source: Path, target: Path) -> int:
    source, target = source.resolve(), target.resolve()
    if target.exists():
        raise ValueError("Choose a new export directory; existing snapshots are never overwritten")
    if source == target or source in target.parents or target in source.parents:
        raise ValueError("Export must be separate from source")
    dev_root = (Path.home() / "dev").resolve()
    if target == dev_root or dev_root in target.parents:
        raise ValueError("Generated exports must be outside ~/dev")
    inspect = runpy.run_path(str(source / "scripts/check_source.py"))["inspect"]
    problems = inspect(source)
    if problems:
        raise ValueError("Source hygiene failed: " + "; ".join(problems))
    selected = [Path(name) for name in PUBLIC_FILES]
    selected.extend(Path(".github/workflows") / name for name in PUBLIC_WORKFLOWS)
    for directory in PUBLIC_DIRS:
        base = source / directory
        if not base.is_dir():
            raise ValueError(f"Missing public source directory: {directory}")
        for path in sorted(base.rglob("*")):
            relative = path.relative_to(source)
            if any(part.startswith(".") for part in relative.parts):
                raise ValueError(f"Hidden path in public source directory: {relative}")
            if path.is_file():
                if path.name in ("AGENTS.md", "CLAUDE.md") or path.suffix not in ALLOWED_SUFFIXES:
                    raise ValueError(f"Unapproved public source file: {relative}")
                selected.append(relative)
    for relative in selected:
        path = source / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing or unsafe public file: {relative}")
    target.mkdir(parents=True)
    for relative in selected:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)
    return len(selected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    try:
        count = export_source(args.source, args.target)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Export only, not published: {args.target.resolve()} ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
