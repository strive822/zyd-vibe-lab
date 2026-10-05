"""Bounded diagnostic events; no generic string payload or exception messages."""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType

from .models import ErrorCode, Provider

EVENTS = frozenset(("start", "quit", "refresh_ok", "refresh_failed", "storage_failed", "unexpected_error", "window_layer_restored"))


class DiagnosticLog:
    def __init__(self, data_dir: Path, *, max_bytes: int = 256 * 1024) -> None:
        self.path = data_dir / "logs" / "events.jsonl"
        self.max_bytes = max_bytes
        self.available = True

    def write(self, event: str, *, provider: Provider | None = None, code: ErrorCode | None = None,
              error: BaseException | None = None, traceback: TracebackType | None = None) -> None:
        if event not in EVENTS:
            raise ValueError("Unsupported diagnostic event")
        value: dict[str, object] = {"at": datetime.now(UTC).isoformat(), "event": event}
        if provider is not None:
            value["provider"] = Provider(provider).value
        if code is not None:
            value["code"] = ErrorCode(code).value
        if error is not None:
            value["errorType"] = type(error).__name__[:64]  # Never str(error) or args.
        if traceback is not None:
            while traceback.tb_next is not None:
                traceback = traceback.tb_next
            value["location"] = Path(traceback.tb_frame.f_code.co_filename).name
            value["line"] = traceback.tb_lineno
        payload = (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists() and self.path.stat().st_size + len(payload) > self.max_bytes:
                os.replace(self.path, self.path.with_suffix(".jsonl.1"))
            with self.path.open("ab") as file:
                file.write(payload)
            self.available = True
        except OSError:
            self.available = False  # Logging failure cannot crash a quota read.
