import json
import subprocess
from types import SimpleNamespace

import pytest

from usage_app import startup_registry as registry
from usage_app.storage import StorageError


@pytest.fixture(autouse=True)
def windows_process_context(monkeypatch):
    # These tests replace subprocess.run; no Windows desktop or registry is used.
    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    monkeypatch.setattr(registry.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)


def test_bridge_rejects_failure_invalid_result_and_missing_response(tmp_path, monkeypatch):
    monkeypatch.setattr(registry.Path, "home", lambda: tmp_path)
    def complete_with(result=None, returncode=0):
        def run(*args, **kwargs):
            folder = next(tmp_path.glob(".usage-startup-*"))
            if result is not None:
                (folder / "response.json").write_text(json.dumps(result), encoding="utf-8")
            return SimpleNamespace(returncode=returncode)
        monkeypatch.setattr(registry.subprocess, "run", run)
    complete_with(returncode=1)
    with pytest.raises(StorageError, match="无法访问"):
        registry.registry_request("read")
    complete_with({"ok": False, "value": "not verified"})
    with pytest.raises(StorageError, match="核验"):
        registry.registry_request("write", "expected")
    complete_with({"ok": True, "value": 42})
    with pytest.raises(StorageError, match="格式"):
        registry.registry_request("read")
    complete_with()
    clock = iter((0, 11))
    monkeypatch.setattr(registry.time, "monotonic", lambda: next(clock))
    with pytest.raises(StorageError, match="超时"):
        registry.registry_request("read")
    assert not list(tmp_path.glob(".usage-startup-*"))


def test_bridge_timeout_is_storage_failure_and_temp_messages_are_removed(tmp_path, monkeypatch):
    monkeypatch.setattr(registry.Path, "home", lambda: tmp_path)
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("powershell", 10)
    monkeypatch.setattr(registry.subprocess, "run", timeout)
    with pytest.raises(StorageError, match="核验"):
        registry.registry_request("write", "expected")
    assert not list(tmp_path.glob(".usage-startup-*"))


@pytest.mark.parametrize("winerror", [5, 32, 33])
def test_atomic_response_briefly_locked_by_windows_is_read_within_deadline(tmp_path, monkeypatch, winerror):
    monkeypatch.setattr(registry.Path, "home", lambda: tmp_path)
    def run(*args, **kwargs):
        folder = next(tmp_path.glob(".usage-startup-*"))
        (folder / "response.json").write_text('{"ok": true, "value": "verified"}', encoding="utf-8")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(registry.subprocess, "run", run)
    original = registry.Path.read_text
    calls = []
    def read(path, *args, **kwargs):
        calls.append(path.name)
        if len(calls) == 1:
            error = PermissionError("transient Windows sharing conflict")
            error.winerror = winerror
            raise error
        return original(path, *args, **kwargs)
    monkeypatch.setattr(registry.Path, "read_text", read)
    assert registry.registry_request("read") == "verified"
    assert len(calls) == 2 and not list(tmp_path.glob(".usage-startup-*"))


def test_persistent_response_access_failure_times_out_and_cleans_up(tmp_path, monkeypatch):
    monkeypatch.setattr(registry.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    def denied(*args, **kwargs):
        error = PermissionError("persistent Windows sharing conflict")
        error.winerror = 32
        raise error
    monkeypatch.setattr(registry.Path, "read_text", denied)
    clock = iter((0, 11))
    monkeypatch.setattr(registry.time, "monotonic", lambda: next(clock))
    with pytest.raises(StorageError, match="超时"):
        registry.registry_request("read")
    assert not list(tmp_path.glob(".usage-startup-*"))
