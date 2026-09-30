"""Own-Qt regression for independent settings, cancelled clicks and lost leave timers."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from PySide6.QtCore import QEvent, QEventLoop, QPoint, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from usage_app.desktop import DesktopLeaf
from usage_app.runtime import UsageRuntime


def pump(milliseconds):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def main():
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    checks = {}
    with tempfile.TemporaryDirectory(prefix="duizhaoye-collapse-check-") as directory:
        runtime = UsageRuntime(Path(directory))
        runtime.stop()
        leaf = DesktopLeaf(runtime, reduced_motion=True)
        leaf.show()
        leaf.set_expansion_progress(1)
        leaf._visible_hit = lambda x, y: False  # No physical pointer is moved.
        leaf._last_inside = False
        leaf._open_settings("accounts")
        panel = leaf.text_settings
        QApplication.sendEvent(panel, QEvent(QEvent.Type.WindowActivate))
        pump(1100)
        checks["independent active settings remains visible while leaf automatically collapses"] = panel.isVisible() and not leaf._auxiliary_open and leaf._progress == 0
        panel.hide()
        pump(60)

        # Qt can give mouse/activation focus before a cancelled release. Model
        # just that focus ownership; inject events only into this owned widget.
        focused = {"value": True}
        clear = leaf.clearFocus
        leaf.hasFocus = lambda: focused["value"]
        def release_focus():
            focused["value"] = False
            clear()
        leaf.clearFocus = release_focus
        leaf.set_expansion_progress(1)
        leaf._last_inside = True
        leaf._close_timer.stop()
        centre = leaf._ball_center(0).toPoint()
        QTest.mousePress(leaf, Qt.MouseButton.LeftButton, pos=centre)
        QTest.mouseRelease(leaf, Qt.MouseButton.LeftButton, pos=QPoint(-50, -50))
        leaf._check_cursor_and_animate()
        pump(1100)
        checks["cancelled action press releases mouse focus and collapses without activating a copy"] = not focused["value"] and not leaf._drag_pending and leaf._progress == 0 and not leaf.copy_feedback

        focused["value"] = False
        leaf.set_expansion_progress(1)
        leaf._last_inside = False
        leaf._close_timer.stop()
        leaf._pulse.start(32)
        pump(1100)
        checks["outside expanded state re-arms a missing leave timer once without postponing its deadline"] = leaf._progress == 0 and leaf._pulse.isActive()

        leaf.set_explicit_pin(True)
        leaf._check_cursor_and_animate()
        pump(900)
        checks["explicit user pin remains expanded"] = leaf._progress == 1 and leaf._explicit_pin
        leaf.set_explicit_pin(False)
        leaf._focus_next(1)
        leaf._check_cursor_and_animate()
        pump(900)
        checks["deliberate keyboard navigation remains expanded"] = leaf._progress == 1 and leaf.keyboard_ball == 0
        leaf.quit_app()
    out = Path("evidence/m6/collapse-native-result.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {"passed": sum(checks.values()), "checks": checks, "nativeDpr": app.primaryScreen().devicePixelRatio(),
              "boundary": "Real owned Qt windows and programmatic Qt events/logical cursor/focus fixtures. No physical mouse injection. Actual intermittent desktop behavior still needs user confirmation."}
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
