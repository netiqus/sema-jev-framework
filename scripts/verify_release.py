"""Check tag, package and import versions before producing a draft release."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import tomllib
from pathlib import Path


def verify_release(root: Path, tag: str) -> None:
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:(?:a|b|rc)[0-9]+)?", tag):
        raise ValueError("Use a version tag such as v0.2.0a1 or v1.0.0")
    tag_commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"], cwd=root, text=True
    ).strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if tag_commit != head:
        raise ValueError("Select the exact tagged ref when dispatching the release")
    version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    tree = ast.parse((root / "src/sema_jev/__init__.py").read_text())
    imported_version = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        )
    )
    if tag != "v" + version or imported_version != version:
        raise ValueError("Tag, package and import versions must match")


if __name__ == "__main__":
    try:
        verify_release(Path.cwd(), os.environ["RELEASE_TAG"])
    except (ValueError, KeyError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc)) from exc
    print("Release tag, package and import versions match")
