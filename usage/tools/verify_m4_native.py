"""Real Windows widget/file/clipboard probes; physical Notepad editing is separate."""
from __future__ import annotations

from _paths import EVIDENCE

import ctypes
import json
import os
import sys
import tempfile
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QEventLoop, QPoint, QProcess, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from usage_app.clipboard import WindowsClipboard, windows_text
from usage_app.desktop import DesktopLeaf
from usage_app.runtime import UsageRuntime
from usage_app.snippets import ContentStatus


def pump(milliseconds: int = 150) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def owned_clipboard_text() -> str:
    api = WindowsClipboard()
    assert api.user.OpenClipboard(None)
    try:
        handle = api.user.GetClipboardData(13)
        pointer = api.memory.GlobalLock(handle)
        assert pointer
        try:
            return ctypes.wstring_at(pointer)
        finally:
            api.memory.GlobalUnlock(handle)
    finally:
        api.user.CloseClipboard()


def main() -> int:
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    out = Path(EVIDENCE / "m4") / str(round(app.primaryScreen().devicePixelRatio() * 100))
    out.mkdir(parents=True, exist_ok=True)
    checks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="duizhaoye-m4-check-") as directory:
        runtime = UsageRuntime(Path(directory))
        runtime.stop()
        leaf = DesktopLeaf(runtime, reduced_motion=True)
        leaf._pulse.stop()
        leaf.set_expansion_progress(1)
        leaf.show()
        service = leaf.snippets
        leaf.open_text_settings()
        panel = leaf.text_settings
        assert panel is not None
        pump()
        panel.grab().save(str(out / "settings-empty.png"))
        QTest.keyClicks(panel.name, "review")
        panel.name.setText("代码评审")
        panel.description.setText("检查输入边界、失败恢复与可维护性")
        panel.icons.setCurrentIndex(2)
        panel.favorite.setCurrentIndex(1)
        panel.save_button.click()
        assert len(service.items) == 1
        a = service.items[0]
        body = "  中文 English 😀 e\u0301\r\n\t第二行  \n尾行 "
        service.store.path_for(a).write_bytes(body.encode())
        pump(300)
        assert panel.preview.toPlainText() == body.replace("\r\n", "\n")
        assert service.read(a.id).text == body
        panel.name.setFocus()
        panel.grab().save(str(out / "settings-saved.png"))
        checks.append("form add + stable ID + saved UTF-8 preview")
        panel.name.setText("尚未保存的改名")
        leaf.save_placement()
        pump(220)
        assert panel.name.text() == "尚未保存的改名"
        checks.append("unrelated placement write preserves metadata draft")
        panel.save_button.click()
        assert service.items[0].id == a.id and service.read(a.id).text == body
        b = service.store.add("第二条文本", "独立正文与第二常用位", "text", 1)
        service.store.path_for(b).write_bytes("第二条 另一个正文".encode())
        for i in range(12):
            service.store.add(f"备用文本 {i + 1}", "具名条目，不会挤入浮窗", "note")
        service.reload()
        panel.hide()
        leaf._activate_ball(0)
        assert leaf.copy_feedback == "已复制" and leaf._copy_confirmed(0) and not leaf._copy_confirmed(1)
        assert owned_clipboard_text() == windows_text(body)
        leaf.grab().save(str(out / "copy-first.png"))
        leaf._activate_ball(1)
        assert owned_clipboard_text() == "第二条 另一个正文" and leaf._copy_confirmed(1)
        checks.append("two named balls write verified CF_UNICODETEXT with correct feedback")
        holder = QProcess()
        code = "import ctypes,sys; from PySide6.QtWidgets import QApplication,QWidget; app=QApplication([]); window=QWidget(); user=ctypes.WinDLL('user32'); user.OpenClipboard.argtypes=[ctypes.c_void_p]; assert user.OpenClipboard(int(window.winId())); print('locked',flush=True); sys.stdin.readline(); user.CloseClipboard()"
        holder.start(sys.executable, ["-c", code])
        try:
            assert holder.waitForReadyRead(3000)
            assert holder.readAllStandardOutput().data().strip() == b"locked"
            leaf._activate_ball(0)
            assert leaf.copy_feedback == "复制失败" and "占用" in leaf._copy_result.message
            leaf.grab().save(str(out / "copy-busy.png"))
        finally:
            holder.write(b"release\n")
            holder.closeWriteChannel()
            assert holder.waitForFinished(3000)
        assert owned_clipboard_text() == "第二条 另一个正文"
        checks.append("another native process holds clipboard: explicit failure, prior body preserved")
        leaf.open_more_texts()
        more = leaf.more_texts
        assert more is not None and leaf._auxiliary_open
        pump()
        more.grab().save(str(out / "more-selected.png"))
        more.list.setCurrentRow(1)
        QTest.keyClick(more.list, Qt.Key.Key_Return)
        assert owned_clipboard_text() == "第二条 另一个正文"
        assert more.isVisible() and not panel.isVisible()
        api = ctypes.WinDLL("user32.dll")
        api.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        api.SendMessageW.restype = wintypes.LPARAM
        point = more.list.viewport().mapToGlobal(QPoint(80, 80))
        ratio = more.devicePixelRatioF()
        px, py = round(point.x() * ratio), round(point.y() * ratio)
        before = more.list.verticalScrollBar().value()
        api.SendMessageW(int(more.list.viewport().winId()), 0x020A, ((-120) & 0xffff) << 16, (px & 0xffff) | ((py & 0xffff) << 16))
        pump()
        assert more.list.verticalScrollBar().value() > before
        more.grab().save(str(out / "more-scrolled.png"))
        more.hide()
        assert not leaf._auxiliary_open, (leaf._visible_panels, panel.isVisible(), more.isVisible())
        leaf.clearFocus()
        leaf.collapse()
        assert leaf._progress == 0
        leaf.set_expansion_progress(1)
        checks.append("named list Enter copy + native WM_MOUSEWHEEL + leave lock release")
        leaf.open_text_settings()
        panel.list.setCurrentRow(0)
        path = service.store.path_for(a)
        temporary = path.with_suffix(".saving")
        temporary.write_bytes("原子保存后的内容 😀".encode())
        os.replace(temporary, path)
        pump(320)
        assert panel.preview.toPlainText() == "原子保存后的内容 😀"
        path.unlink()
        pump(320)
        assert "删除" in panel.status.text() and not panel.preview.toPlainText()
        panel.grab().save(str(out / "settings-missing.png"))
        path.write_bytes("恢复文件".encode())
        pump(320)
        assert panel.preview.toPlainText() == "恢复文件"
        assert service.read(b.id).text == "第二条 另一个正文"
        checks.append("atomic replacement, missing file and recreation rearm without cross-item content")
        panel.new_item()
        panel.name.setText("长名字 · " + "中文界面与Unicode边界" * 6)
        panel.description.setText("长说明 " * 45)
        panel.save_button.click()
        pump()
        panel.grab().save(str(out / "settings-long.png"))
        leaf._focus_next(1)
        leaf._focus_next(1)
        leaf._focus_next(1)
        leaf._focus_next(1)
        leaf._clear_feedback()
        leaf.grab().save(str(out / "action-focus.png"))
        assert service.read(b.id).status == ContentStatus.READY
        panel.hide()
        service.stop()
        leaf.reminders.stop()
        leaf.tray.hide()
        leaf._quitting = True
        leaf.close()
    report = {"passed": len(checks), "checks": checks, "nativeDpr": app.primaryScreen().devicePixelRatio(),
              "boundary": "Actual Windows Qt windows, native Unicode clipboard and lock holder, saved-file notifications and native wheel. Form/keyboard inputs programmatic. Physical Notepad Ctrl+S, multiple tabs and mouse flow still need user verification."}
    (out / "native-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
