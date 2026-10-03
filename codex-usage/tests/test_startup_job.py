import pytest

from usage_app.autostart import Autostart
from usage_app.startup_job import StartupJob
from usage_app.storage import StorageError


class Registry:
    def __init__(self):
        self.value = None
        self.reads = 0
        self.writes = []

    def read(self):
        self.reads += 1
        return self.value

    def write(self, value):
        self.writes.append(value)
        self.value = value


def test_job_construction_is_lazy_and_read_never_registers(tmp_path):
    registry = Registry()
    job = StartupJob(Autostart(tmp_path, registry))
    results = []
    job.result.finished.connect(lambda value, error: results.append((value, error)))
    assert registry.reads == 0 and not registry.writes
    job.run()
    assert results == [(False, "")]
    assert registry.reads == 1 and not registry.writes


@pytest.mark.parametrize("enabled", [False, True])
def test_explicit_save_completes_only_after_exact_readback(tmp_path, enabled):
    registry = Registry()
    startup = Autostart(tmp_path, registry)
    registry.value = startup.command if not enabled else None
    job = StartupJob(startup, enabled)
    results = []
    job.result.finished.connect(lambda value, error: results.append((value, error)))
    assert not registry.writes
    job.run()
    assert results == [(enabled, "")]
    assert registry.value == (startup.command if enabled else None)


@pytest.mark.parametrize("enabled", [None, True])
def test_read_or_save_failure_returns_visible_error(tmp_path, enabled):
    class Denied(Registry):
        def read(self):
            raise StorageError("无法访问开机启动设置")
    registry = Denied()
    job = StartupJob(Autostart(tmp_path, registry), enabled)
    results = []
    job.result.finished.connect(lambda value, error: results.append((value, error)))
    job.run()
    assert results == [(False, "无法访问开机启动设置")]
    assert not registry.writes


def test_lost_write_is_not_reported_as_saved(tmp_path):
    class Lost(Registry):
        def write(self, value):
            pass
    job = StartupJob(Autostart(tmp_path, Lost()), True)
    results = []
    job.result.finished.connect(lambda value, error: results.append((value, error)))
    job.run()
    assert len(results) == 1 and results[0][0] is False and "核验" in results[0][1]


def test_unexpected_worker_failure_returns_safe_error_instead_of_staying_busy(tmp_path):
    class Broken(Registry):
        def read(self):
            raise RuntimeError("private synthetic diagnostic")
    job = StartupJob(Autostart(tmp_path, Broken()))
    results = []
    job.result.finished.connect(lambda value, error: results.append((value, error)))
    job.run()
    assert results == [(False, "开机启动设置未能完成，请重新打开此页重试。")]
