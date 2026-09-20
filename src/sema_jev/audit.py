"""Optional metadata-only JSONL audit. No input content is persisted."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from .models import Decision
from .policy import ConfigurationError


class JsonlAudit:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser().resolve()
        source = (Path.home() / "dev").resolve()
        if self.path == source or source in self.path.parents:
            raise ConfigurationError("Audit files must not be written inside ~/dev")
        self._lock = threading.Lock()

    def write(self, decision: Decision) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(decision.audit_record(), ensure_ascii=False) + "\n"
        with self._lock:
            fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as stream:
                stream.write(line)
