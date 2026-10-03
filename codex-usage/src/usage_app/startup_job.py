"""Run desktop startup I/O in Qt's worker pool, returning only safe UI results."""
from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from .autostart import Autostart
from .messages import product_message
from .storage import StorageError


class StartupResult(QObject):
    finished = Signal(bool, str)


class StartupJob(QRunnable):
    def __init__(self, startup: Autostart, enabled: bool | None = None) -> None:
        super().__init__()
        self.startup = startup
        self.enabled = enabled
        self.result = StartupResult()

    @Slot()
    def run(self) -> None:
        try:
            if self.enabled is None:
                enabled = self.startup.enabled()
            else:
                self.startup.set_enabled(self.enabled)
                enabled = self.enabled
        except StorageError as error:
            self.result.finished.emit(False, product_message(error))
        except Exception:
            # Worker exceptions must restore the controls without exposing raw
            # OS errors or leaving the form stuck in a saving state.
            self.result.finished.emit(False, "开机启动设置未能完成，请重新打开此页重试。")
        else:
            self.result.finished.emit(enabled, "")
