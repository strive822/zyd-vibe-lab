"""Explicit current-user startup opt-in; no task scheduler or system-wide keys."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Protocol

from .storage import StorageError
from .startup_registry import registry_request

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "Duizhaoye"


class StartupRegistry(Protocol):
    def read(self) -> str | None: ...
    def write(self, value: str | None) -> None: ...


class UserRunRegistry:
    def read(self) -> str | None:
        return registry_request("read")

    def write(self, value: str | None) -> None:
        if registry_request("write", value) != value:
            raise StorageError("开机启动项未能核验，请重新打开设置检查")


def startup_command(data_dir: Path) -> str:
    executable = Path(sys.executable).resolve()
    root = executable.parent.parent
    script = Path(__file__).resolve().parent.parent / "run_app.py"
    launcher = root / "usage.exe"
    if executable.parent.name == "runtime" and script.parent == root / "app" and launcher.is_file():
        return subprocess.list2cmdline([str(launcher), "--data-dir", str(data_dir.resolve())])
    windowed = executable.with_name("pythonw.exe")
    if windowed.exists():
        executable = windowed
    return subprocess.list2cmdline([str(executable), str(script), "--data-dir", str(data_dir.resolve())])


class Autostart:
    def __init__(self, data_dir: Path, registry: StartupRegistry | None = None):
        self.command = startup_command(data_dir)
        self.registry = registry or UserRunRegistry()

    def enabled(self) -> bool:
        return self.registry.read() is not None

    def set_enabled(self, enabled: bool) -> None:
        # Called only from an explicit settings save. Construction/read never writes.
        if enabled and len(self.command.encode("utf-16-le")) // 2 > 260:
            raise StorageError("安装路径过长，Windows 无法可靠执行启动项；请将程序移到较短的路径后再启用")
        previous = self.registry.read()
        expected = self.command if enabled else None
        if previous != expected:
            self.registry.write(expected)
        if self.registry.read() != expected:
            raise StorageError("开机启动项未能核验，请重新打开设置检查")
