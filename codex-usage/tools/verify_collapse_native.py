"""Own-Qt regression for copy completion, settings and leave reconciliation."""
from __future__ import annotations

from _paths import EVIDENCE

import json
import tempfile
from pathlib import Path

from PySide6.QtCore import QEvent, QEventLoop, QPoint, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from usage_app.desktop import DesktopLeaf
from usage_app.clipboard import ClipboardError
from usage_app.runtime import UsageRuntime


def pump(milliseconds):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def main():
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    checks = {}
    out = Path(EVIDENCE / "m6/more-copy")
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="duizhaoye-collapse-check-") as directory:
        runtime = UsageRuntime(Path(directory))
        runtime.stop()
        leaf = DesktopLeaf(runtime, reduced_motion=True)
        leaf.tray.hide()
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
        leaf._reset_keyboard_focus()
        leaf.pinned = False
        leaf.clearFocus()

        service = leaf.snippets
        first = service.store.add("第一条 · 中文", favorite_slot=0)
        second = service.store.add("第二条")
        service.store.path_for(first).write_bytes("第一份正文\n第二行".encode("utf-8"))
        service.store.path_for(second).write_bytes("第二份正文".encode("utf-8"))
        service.reload()
        written = []
        service.clipboard.write = lambda owner, text: written.append(text)
        for edge in ("right", "left", "top", "bottom"):
            leaf.reduced_motion = edge == "right"
            leaf.set_dock_edge(edge)
            leaf.set_expansion_progress(1)
            leaf.open_more_texts()
            more = leaf.more_texts
            pump(80)
            if edge == "right":
                more.grab().save(str(out / "before-list.png"))
                leaf.grab().save(str(out / "before-leaf.png"))
            row = more.list.item(0)
            QTest.mouseClick(more.list.viewport(), Qt.MouseButton.LeftButton,
                             pos=more.list.visualItemRect(row).center())
            pump(300)
            checks[f"{edge} mouse copy closes list, releases anchor and finishes collapse"] = (
                written[-1] == "第一份正文\n第二行" and not more.isVisible()
                and not leaf._auxiliary_open and leaf._progress == 0 and leaf.keyboard_ball == -1)
            if edge == "right":
                leaf.grab().save(str(out / "after-leaf.png"))
            # Reuse the same panel and select another stable ID with Enter.
            leaf.set_expansion_progress(1)
            leaf.open_more_texts()
            more.list.setCurrentRow(1)
            QTest.keyClick(more.list, Qt.Key.Key_Return)
            pump(300)
            checks[f"{edge} reopened list Enter copies another body without opening settings"] = (
                written[-1] == "第二份正文" and not more.isVisible()
                and leaf._progress == 0 and not panel.isVisible())

        leaf.reduced_motion = True
        leaf.set_dock_edge("right")
        leaf.set_expansion_progress(1)
        leaf.open_more_texts()
        more = leaf.more_texts
        def clipboard_busy(owner, text):
            raise ClipboardError("剪贴板占用，请重试")
        service.clipboard.write = clipboard_busy
        previous = list(written)
        QTest.keyClick(more.list, Qt.Key.Key_Return)
        pump(900)
        checks["failed copy keeps list, error and expanded anchor; previous body preserved"] = (
            more.isVisible() and leaf._auxiliary_open and leaf._progress == 1
            and "占用" in more.status.text() and written == previous and not panel.isVisible())
        more.grab().save(str(out / "copy-error.png"))
        service.clipboard.write = lambda owner, text: written.append(text)
        QTest.keyClick(more.list, Qt.Key.Key_Return)
        checks["retry after failure closes the existing panel and collapses"] = (
            not more.isVisible() and not leaf._auxiliary_open and leaf._progress == 0
            and written[-1] == "第二份正文")

        leaf.set_expansion_progress(1)
        leaf._activate_ball(0)
        checks["favorite copy still shows feedback and uses ordinary leave collapse"] = (
            leaf._progress == 1 and leaf.copy_feedback == "已复制" and written[-1] == "第一份正文\n第二行")
        leaf._check_cursor_and_animate()
        pump(1100)
        checks["favorite copy still collapses on leave"] = leaf._progress == 0
        leaf.set_explicit_pin(True)
        leaf.open_more_texts()
        QTest.keyClick(more.list, Qt.Key.Key_Return)
        checks["successful list copy closes panel but respects explicit fixed expansion"] = (
            not more.isVisible() and not leaf._auxiliary_open and leaf._progress == 1 and leaf._explicit_pin)
        leaf.set_explicit_pin(False)
        leaf.set_dock_edge(None)
        leaf.set_expansion_progress(1)
        leaf.open_more_texts()
        QTest.keyClick(more.list, Qt.Key.Key_Return)
        checks["free placement closes copied list and retains its existing visible layout"] = (
            not more.isVisible() and not leaf._auxiliary_open and leaf._progress == 1)
        leaf.quit_app()
    report = {"passed": sum(checks.values()), "checks": checks, "nativeDpr": app.primaryScreen().devicePixelRatio(),
              "boundary": "Real owned Qt windows and programmatic Qt events/logical cursor/focus fixtures. No physical mouse injection. Actual intermittent desktop behavior still needs user confirmation."}
    (out / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
