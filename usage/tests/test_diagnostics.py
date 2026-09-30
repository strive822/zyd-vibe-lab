import json
import sys

import pytest

from usage_app.diagnostics import DiagnosticLog
from usage_app.models import ErrorCode, Provider


def test_exception_body_and_trace_source_never_enter_log(tmp_path):
    log = DiagnosticLog(tmp_path)
    try:
        raise RuntimeError("private-key-and-snippet-body")
    except RuntimeError as error:
        log.write("unexpected_error", error=error, traceback=sys.exc_info()[2])
    raw = log.path.read_text(encoding="utf-8")
    value = json.loads(raw)
    assert "private-key" not in raw and "snippet-body" not in raw
    assert value["errorType"] == "RuntimeError" and value["location"] == "test_diagnostics.py"
    log.write("refresh_failed", provider=Provider.GLM, code=ErrorCode.AUTH_REQUIRED)
    with pytest.raises(ValueError):
        log.write("unapproved-raw-response")


def test_rotation_bounded_and_permission_failure_does_not_escape(tmp_path, monkeypatch):
    log = DiagnosticLog(tmp_path, max_bytes=180)
    for _ in range(20):
        log.write("refresh_ok", provider=Provider.CODEX)
    assert log.path.stat().st_size <= 180
    assert log.path.with_suffix(".jsonl.1").stat().st_size <= 180
    def denied(*args, **kwargs):
        raise PermissionError()
    monkeypatch.setattr(type(log.path), "open", denied)
    log.write("quit")
    assert not log.available
