"""Check local public Markdown links and required bilingual file pairs."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


def inspect(root: Path) -> list[str]:
    documents = [
        *root.glob("*.md"),
        *root.glob("docs/**/*.md"),
        *root.glob("examples/**/*.md"),
        *root.glob("evals/**/*.md"),
    ]
    failures = []
    for document in documents:
        if document.name in ("AGENTS.md", "CLAUDE.md"):
            continue
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", text):
            parsed = urlsplit(target)
            if parsed.scheme or not parsed.path or parsed.path.startswith("/"):
                continue
            destination = document.parent / unquote(parsed.path)
            if not destination.exists():
                failures.append(f"{document.relative_to(root)}: broken link {target}")
    for path in [*documents, *root.glob("examples/**/*.txt")]:
        for language, other in (("cz", "en"), ("en", "cz")):
            ending = f".{language}{path.suffix}"
            if path.name.endswith(ending):
                peer = path.with_name(path.name.removesuffix(ending) + f".{other}{path.suffix}")
                if not peer.is_file():
                    failures.append(f"{path.relative_to(root)}: missing {other} counterpart")
                elif path.suffix == ".md" and peer.name not in path.read_text(encoding="utf-8"):
                    failures.append(f"{path.relative_to(root)}: missing counterpart link")
    for entry in ("README", "CHANGELOG", "CONTRIBUTING", "examples/news/README", "evals/README"):
        primary = root / f"{entry}.md"
        english = root / f"{entry}.en.md"
        if primary.read_bytes() != english.read_bytes():
            failures.append(f"{entry}.md: keep the default entry equal to its English version")
    return failures


if __name__ == "__main__":
    problems = inspect(Path.cwd())
    for problem in problems:
        print(problem)
    print("Documentation links and language pairs: " + ("FAIL" if problems else "PASS"))
    raise SystemExit(bool(problems))
