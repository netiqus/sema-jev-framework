"""Reject runtime artifacts and obvious credentials in source; report paths only."""

from __future__ import annotations

import re
import sys
from pathlib import Path

BAD_DIRS = {
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
}
SECRET = re.compile(
    r"(?:sk-or-v1-[a-zA-Z0-9]{16,}|gh[pousr]_[a-zA-Z0-9]{20,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)"
)


def inspect(root: Path) -> list[str]:
    failures = []
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if ".git" in rel.parts:
            continue
        if path.is_symlink():
            failures.append(str(rel) + ": symlink not allowed in source exports")
            continue
        if path.is_dir() and path.name in BAD_DIRS:
            failures.append(str(rel) + ": runtime directory")
        if not path.is_file():
            continue
        if path.name.startswith(".env") and not path.name.endswith(".example"):
            failures.append(str(rel) + ": filled environment file")
        if path.suffix in (".log", ".pyc", ".pem", ".key") or path.name == "runtime.env":
            failures.append(str(rel) + ": runtime or credential file")
        if path.stat().st_size < 2_000_000:
            try:
                if SECRET.search(path.read_text(encoding="utf-8")):
                    failures.append(str(rel) + ": credential pattern")
            except UnicodeError:
                failures.append(str(rel) + ": unexpected binary file")
    return failures


if __name__ == "__main__":
    found = inspect(Path(sys.argv[1]).resolve())
    for problem in found:
        print(problem, file=sys.stderr)
    print("Source hygiene: " + ("FAIL" if found else "PASS"))
    raise SystemExit(bool(found))
