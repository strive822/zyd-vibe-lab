"""Settings save/error probes with fake startup storage; never registers startup."""
from __future__ import annotations

from _paths import EVIDENCE

import ctypes
import json
import tempfile
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QEvent, QEventLoop, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

from usage_app.autostart import Autostart, UserRunRegistry
from usage_app.desktop import DesktopLeaf
from usage_app.runtime import UsageRuntime
from usage_app.storage import StorageError
from usage_app.window_ui import WindowPage


class FakeRegistry:
    value = None
    def read(self):
        return self.value
    def write(self, value):
        self.value = value


def pump(milliseconds=120):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def main() -> int:
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    out = Path(EVIDENCE / "m5") / str(round(app.primaryScreen().devicePixelRatio() * 100))
    out.mkdir(parents=True, exist_ok=True)
    checks = []
    original_startup = UserRunRegistry().read()
    with tempfile.TemporaryDirectory(prefix="duizhaoye-window-check-") as directory:
        runtime = UsageRuntime(Path(directory))
        runtime.stop()
        leaf = DesktopLeaf(runtime, reduced_motion=True)
        leaf._pulse.stop()
        registry = FakeRegistry()
        leaf.startup = Autostart(Path(directory), registry)
        leaf.show()
        leaf._open_settings("window")
        panel = leaf.text_settings
        page = panel.findChild(WindowPage)
        assert page is not None
        pump()
        user = ctypes.WinDLL("user32", use_last_error=True)
        user.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
        user.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        user.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
        user.GetWindow.restype = wintypes.HWND
        user.IsIconic.argtypes = [wintypes.HWND]
        user.IsIconic.restype = wintypes.BOOL
        user.GetTopWindow.argtypes = [wintypes.HWND]
        user.GetTopWindow.restype = wintypes.HWND
        handle = int(panel.winId())
        assert not user.GetWindowLongPtrW(handle, -20) & 0x00000008  # WS_EX_TOPMOST
        assert not user.GetWindow(handle, 4)  # Independent, no topmost owner.
        style = user.GetWindowLongPtrW(handle, -16)
        assert style & 0x00020000 and style & 0x00010000  # Native minimize/maximize boxes.
        QApplication.sendEvent(panel, QEvent(QEvent.Type.WindowActivate))
        assert not leaf._auxiliary_open
        QApplication.sendEvent(panel, QEvent(QEvent.Type.WindowDeactivate))
        assert not leaf._auxiliary_open
        panel.showMinimized()
        pump()
        assert user.IsIconic(handle) and leaf.isVisible()
        panel.showNormal()
        other = QWidget()
        other.setWindowTitle("usage · 普通窗口层级验证")
        other.setGeometry(panel.geometry())
        other.show()
        other.raise_()
        other.activateWindow()
        pump()
        # Background-process foreground requests may be refused by Windows.
        # Read the actual Z-order instead of asserting screen-pixel ownership
        # over whichever unrelated foreground application the user is using.
        current = user.GetTopWindow(None)
        while current and int(current) not in (handle, int(other.winId())):
            current = user.GetWindow(current, 2)  # GW_HWNDNEXT, read only.
        assert int(current) == int(other.winId())
        other.close()
        panel.raise_()
        panel.activateWindow()
        pump()
        checks.append("independent non-topmost settings uses native minimize/maximize and permits another normal window above it; editor activation never locks the leaf")
        panel.grab().save(str(out / "window-normal.png"))
        page.reduced.setChecked(False)
        page.pinned.setChecked(True)
        page.launch.setChecked(True)
        QTest.keyClick(page.save_button, Qt.Key.Key_Return)
        assert leaf._explicit_pin and not leaf.reduced_motion
        assert leaf._settings.load().placement.pinned and not leaf._settings.load().reduced_motion
        assert registry.value == leaf.startup.command
        checks.append("explicit Enter save persists pin/motion and verifies opt-in in isolated fake registry")
        saved = leaf._settings.save
        def fail(value):
            raise StorageError("synthetic save failure")
        leaf._settings.save = fail
        page.reduced.setChecked(True)
        page.pinned.setChecked(False)
        page.save_button.click()
        assert "未能保存" in page.status.text()
        assert leaf._settings.load().placement.pinned
        pump()
        panel.grab().save(str(out / "window-save-error.png"))
        leaf._settings.save = saved
        page.save_button.click()
        assert leaf._settings.load().reduced_motion and not leaf._settings.load().placement.pinned
        checks.append("failure preserves saved state; retry succeeds without false success")
        panel.select_section("texts")
        leaf.set_explicit_pin(True)
        panel.select_section("window")
        assert page.pinned.isChecked()
        panel.resize(560, 480)
        pump()
        panel.grab().save(str(out / "window-small.png"))
        checks.append("current desktop shortcut state appears when section is reopened; minimum size scrolls")
        leaf.reminders.stop()
        leaf.snippets.stop()
        panel.hide()
        leaf.tray.hide()
        leaf._quitting = True
        leaf.close()
    assert UserRunRegistry().read() == original_startup
    checks.append("real current-user startup entry unchanged throughout test")
    report = {"passed": len(checks), "checks": checks, "nativeDpr": app.primaryScreen().devicePixelRatio(),
              "boundary": "Real Qt form, actual settings atomic persistence and native key events. Startup writes use a fake registry; real registry only compared before/after. Physical login startup remains unverified."}
    (out / "window-native-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
