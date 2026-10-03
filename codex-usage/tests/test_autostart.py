import pytest

from usage_app.autostart import Autostart, startup_command
from usage_app.storage import StorageError
import usage_app.autostart as autostart


class MemoryRegistry:
    def __init__(self):
        self.value = None
        self.writes = []

    def read(self):
        return self.value

    def write(self, value):
        self.writes.append(value)
        self.value = value


def test_read_never_registers_and_explicit_opt_in_only_changes_owned_entry(tmp_path):
    registry = MemoryRegistry()
    startup = Autostart(tmp_path, registry)
    assert not startup.enabled() and registry.writes == []
    startup.set_enabled(True)
    assert startup.enabled() and registry.writes == [startup.command]
    startup.set_enabled(True)
    assert len(registry.writes) == 1
    startup.set_enabled(False)
    assert not startup.enabled() and registry.writes[-1] is None


def test_command_quotes_paths_with_spaces_without_shell_execution(tmp_path):
    data_dir = tmp_path / "Test User" / "My Data"
    command = startup_command(data_dir)
    assert '"' + str(data_dir.resolve()) + '"' in command
    assert "run_app.py" in command and "--data-dir" in command


def test_write_failure_and_readback_mismatch_do_not_claim_success(tmp_path):
    class Denied(MemoryRegistry):
        def write(self, value):
            raise StorageError("denied")
    registry = Denied()
    with pytest.raises(StorageError):
        Autostart(tmp_path, registry).set_enabled(True)
    assert registry.value is None
    class Lost(MemoryRegistry):
        def write(self, value):
            pass
    with pytest.raises(StorageError, match="核验"):
        Autostart(tmp_path, Lost()).set_enabled(True)


def test_windows_run_command_limit_rejects_without_registering_and_allows_removal(tmp_path):
    registry = MemoryRegistry()
    startup = Autostart(tmp_path, registry)
    startup.command = "x" * 261
    with pytest.raises(StorageError, match="路径过长"):
        startup.set_enabled(True)
    assert registry.writes == [] and registry.value is None
    registry.value = startup.command
    startup.set_enabled(False)
    assert registry.value is None and registry.writes == [None]


def test_portable_startup_uses_the_windowed_launcher_and_survives_spaces(tmp_path, monkeypatch):
    root = tmp_path / "中文 portable package"
    (root / "runtime").mkdir(parents=True)
    (root / "app/usage_app").mkdir(parents=True)
    (root / "usage.exe").touch()
    monkeypatch.setattr(autostart.sys, "executable", str(root / "runtime/pythonw.exe"))
    monkeypatch.setattr(autostart, "__file__", str(root / "app/usage_app/autostart.py"))
    command = startup_command(tmp_path / "user data")
    assert command.startswith('"' + str(root / "usage.exe") + '" --data-dir ')
    assert "pythonw.exe" not in command and "run_app.py" not in command


def test_registry_adapter_reads_login_view_and_requires_exact_write_readback(monkeypatch):
    calls = []
    def worker(action, value=None):
        calls.append((action, value))
        return "login-visible value" if action == "read" else "wrong"
    monkeypatch.setattr(autostart, "registry_request", worker)
    registry = autostart.UserRunRegistry()
    assert registry.read() == "login-visible value"
    assert calls == [("read", None)]
    with pytest.raises(StorageError, match="核验"):
        registry.write("expected")
