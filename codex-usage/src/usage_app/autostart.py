"""Explicit current-user startup opt-in; no task scheduler or system-wide keys."""
from __future__ import annotations

import subprocess
import sys
import winreg
from pathlib import Path
from typing import Protocol

from .storage import StorageError

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "Duizhaoye"


class StartupRegistry(Protocol):
    def read(self) -> str | None: ...
    def write(self, value: str | None) -> None: ...


class UserRunRegistry:
    def read(self) -> str | None:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                value, kind = winreg.QueryValueEx(key, RUN_NAME)
            if kind != winreg.REG_SZ or not isinstance(value, str):
                raise StorageError("开机启动项格式不兼容，原项已保留")
            return value
        except FileNotFoundError:
            return None
        except OSError as error:
            raise StorageError("无法读取本用户的开机启动项") from error

    def write(self, value: str | None) -> None:
        try:
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, access=winreg.KEY_SET_VALUE) as key:
                if value is None:
                    try:
                        winreg.DeleteValue(key, RUN_NAME)
                    except FileNotFoundError:
                        pass
                else:
                    winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, value)
        except OSError as error:
            raise StorageError("开机启动项未能修改，请检查本用户的权限") from error


def startup_command(data_dir: Path) -> str:
    executable = Path(sys.executable).resolve()
    windowed = executable.with_name("pythonw.exe")
    if windowed.exists():
        executable = windowed
    script = Path(__file__).resolve().parent.parent / "run_app.py"
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
