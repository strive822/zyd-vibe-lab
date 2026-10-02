"""Real Windows/Qt shell checks. Synthetic input is not physical multi-monitor UAT."""
from __future__ import annotations

from _paths import EVIDENCE

import ctypes
import json
import subprocess
import sys
import tempfile
from ctypes import wintypes
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEventLoop, QPoint, QTimer
from PySide6.QtWidgets import QApplication

from usage_app.desktop import DesktopLeaf, SingleInstance, screen_key
from usage_app.desktop_geometry import Placement
from usage_app.runtime import UsageRuntime
from usage_app.rules import BenefitStatus


def pump(milliseconds: int = 100) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def main() -> int:
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    out = Path(EVIDENCE / "m3")
    out.mkdir(parents=True, exist_ok=True)
    checks = []
    with tempfile.TemporaryDirectory(prefix="duizhaoye-m3-check-") as directory:
        root = Path(directory)
        primary = SingleInstance(root)
        assert primary.acquire()
        restored = []
        primary.on_restore(lambda: restored.append(True))
        code = "from pathlib import Path; from PySide6.QtCore import QCoreApplication; from usage_app.desktop import SingleInstance; app=QCoreApplication([]); assert not SingleInstance(Path(__import__('sys').argv[1])).acquire()"
        second = subprocess.Popen([sys.executable, "-c", code, str(root)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for _ in range(30):
            pump(50)
            if second.poll() is not None:
                break
        stdout, stderr = second.communicate(timeout=2)
        assert second.returncode == 0, stderr.decode(errors="replace")
        assert restored == [True]
        checks.append("local-user single instance + restore IPC")
        runtime = UsageRuntime(root)
        runtime.stop()
        original_accounts = runtime.accounts.load()
        widget = DesktopLeaf(runtime, reduced_motion=True)
        widget._pulse.stop()
        widget.show()
        pump()
        assert widget.tray.isVisible()
        checks.append("tray icon submitted")
        for edge in ("left", "right", "top", "bottom"):
            place = Placement(screen_key(app.primaryScreen()), edge, .5, free_orientation=edge)
            widget.apply_placement(place)
            widget.set_expansion_progress(1)
            pump(25)
            widget.grab().save(str(out / f"shell-{edge}.png"))
            widget.save_placement()
            loaded = widget._settings.load()
            assert loaded.placement.edge == edge and abs(loaded.placement.edge_offset_ratio - .5) < .005
            assert runtime.accounts.load() == original_accounts
        checks.append("four edges roundtrip placement without modifying accounts")
        widget.set_explicit_pin(True)
        widget._perform_click(145, 145)
        widget.collapse()
        assert widget._progress == 1 and widget.pinned and widget._explicit_pin
        widget.save_placement()
        assert widget._settings.load().placement.pinned
        checks.append("explicit pin survives click + leave + save")
        widget.hide_to_tray()
        assert not widget.isVisible() and not widget._pulse.isActive()
        widget.restore_from_tray()
        widget._pulse.stop()
        assert widget.isVisible() and widget._progress == 1
        checks.append("hide + restore keeps pin and stops hidden hover polling")
        saved = widget._settings.load().placement
        widget.apply_placement(replace(saved, monitor_key="removed-synthetic-monitor"))
        assert widget.screen() == app.primaryScreen()
        work = widget.screen().availableGeometry()
        assert work.contains(widget.geometry())
        checks.append("missing monitor falls back into primary work area")
        widget._menu.popup(widget.mapToGlobal(QPoint(90, 100)))
        pump(80)
        assert widget._menu_open
        widget.collapse()
        assert widget._progress == 1
        widget._menu.grab().save(str(out / "menu.png"))
        api = ctypes.WinDLL("user32.dll")
        api.WindowFromPoint.argtypes = [wintypes.POINT]
        api.WindowFromPoint.restype = wintypes.HWND
        point = widget._menu.mapToGlobal(QPoint(20, 20))
        ratio = widget._menu.devicePixelRatioF()
        window = api.WindowFromPoint(wintypes.POINT(round(point.x() * ratio), round(point.y() * ratio)))
        assert int(window) == int(widget._menu.winId())
        checks.append("native menu hit remains above topmost widget")
        widget._menu.hide()
        resume = []
        widget.resumed.connect(lambda: resume.append(True))
        message = wintypes.MSG()
        message.message, message.wParam = 0x0218, 0x0012
        widget.nativeEvent(b"windows_generic_MSG", ctypes.addressof(message))
        pump(20)
        assert resume == [True]
        checks.append("Windows resume message reaches refresh coordinator")
        widget.set_explicit_pin(False)
        widget.reduced_motion = False
        widget.apply_placement(Placement(screen_key(app.primaryScreen()), "right", .5))
        widget.set_expansion_progress(0)
        visible_hit = widget._visible_hit
        widget._last_inside = False
        widget._visible_hit = lambda x, y: False
        widget._pulse.start(32)
        widget._check_cursor_and_animate()
        assert widget._pulse.isActive()
        widget._visible_hit = lambda x, y: True  # Logical hit fixture, no injected physical mouse.
        # Deliberately supply NO Enter event: entering an inactive masked tool
        # must still wake through the light polling path.
        pump(500)
        assert widget._progress == 1
        pump(350)
        assert widget._progress == 1  # Stationary logical hit does not oscillate.
        widget._visible_hit = lambda x, y: False
        widget._check_cursor_and_animate()
        pump(1050)
        assert widget._progress == 0 and widget._pulse.isActive()
        widget._visible_hit = visible_hit
        checks.append("quiet dock light polling wakes without Qt Enter, keeps stationary logical hover and original delayed collapse")
        now = widget._now
        widget._now = lambda: datetime.fromisoformat("2026-09-30T17:59:59+08:00")
        widget._on_tick()
        assert widget._dock_benefit_status == (BenefitStatus.STANDARD, BenefitStatus.STANDARD)
        widget._now = lambda: datetime.fromisoformat("2026-09-30T18:00:00+08:00")
        widget._on_tick()
        assert widget._dock_benefit_status == (BenefitStatus.DISCOUNT, BenefitStatus.DISCOUNT)
        widget._now = now
        checks.append("quiet dock updates both distinct benefit marks at the exact ordinary-rule boundary")
        widget.snippets.stop()
        widget.reminders.stop()
        widget.tray.hide()
        widget._quitting = True
        widget.close()
    report = {"passed": len(checks), "checks": checks,
              "nativeDpr": app.primaryScreen().devicePixelRatio(), "screenCount": len(app.screens()),
              "boundary": "Real Windows Qt windows, tray submission, named pipe and native menu hit. Programmatic input/monitor-removal/resume simulation; physical mixed DPI, unplugging and sleep remain unverified."}
    (out / "native-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
