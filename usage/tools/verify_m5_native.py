"""Reminder slice native run; notification submission is not visibility evidence."""
from __future__ import annotations

from _paths import EVIDENCE

import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PySide6.QtCore import QEventLoop, Qt, QTime, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from usage_app.desktop import DesktopLeaf
from usage_app.reminder_service import ClockReading
from usage_app.reminder_ui import ReminderPage
from usage_app.reminders import OccurrenceState
from usage_app.runtime import UsageRuntime


def pump(milliseconds: int = 120) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


class TestClock:
    def __init__(self) -> None:
        self.now = datetime.now(UTC).replace(second=0, microsecond=0)

    def read(self) -> ClockReading:
        return ClockReading(self.now, ZoneInfo("Asia/Shanghai"), "中国标准时间")


def main() -> int:
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    out = Path(EVIDENCE / "m5") / str(round(app.primaryScreen().devicePixelRatio() * 100))
    out.mkdir(parents=True, exist_ok=True)
    checks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="duizhaoye-m5-check-") as directory:
        runtime = UsageRuntime(Path(directory))
        runtime.stop()
        leaf = DesktopLeaf(runtime, reduced_motion=True)
        leaf._pulse.stop()
        leaf.set_expansion_progress(1)
        leaf.show()
        clock = TestClock()
        leaf.reminders.clock = clock
        leaf.reminders._timer.stop()
        leaf.open_reminders()
        panel = leaf.text_settings
        assert panel is not None
        page = panel.findChild(ReminderPage)
        assert page is not None
        pump()
        panel.grab().save(str(out / "reminders-empty.png"))
        local = clock.now.astimezone(ZoneInfo("Asia/Shanghai"))
        due_at = local + timedelta(minutes=1)
        page.title.setText("usage检查 · 休息一下")
        page.time.setTime(QTime(due_at.hour, due_at.minute))
        page.save_button.click()
        assert len(leaf.reminders.items) == 1 and not leaf.reminders.unread
        identity = leaf.reminders.items[0].id
        page.time.setFocus()
        panel.grab().save(str(out / "reminders-saved-focus.png"))
        checks.append("form saves a real daily definition without an early notification")
        notifications = []
        real_submit = leaf.tray.showMessage
        def submit(title, message, icon, duration):
            assert leaf.reminders.ledger.load()[0].state == OccurrenceState.CLAIMED
            notifications.append((title, message))
            real_submit(title, message, icon, duration)
        leaf.tray.showMessage = submit
        clock.now += timedelta(minutes=1)
        leaf.reminders.poll()
        assert leaf.unread_reminder and len(leaf.reminders.unread) == 1
        if QSystemTrayIcon.supportsMessages():
            assert len(notifications) == 1
            assert leaf.reminders.unread[0].state == OccurrenceState.SUBMITTED
        leaf.reminders.poll()
        assert len(notifications) <= 1
        page.reload_items()
        panel.grab().save(str(out / "reminders-unread.png"))
        panel.hide()
        leaf.set_expansion_progress(0)
        leaf.grab().save(str(out / "dock-unread.png"))
        leaf._activate_ball(leaf._reminder_ball_index())
        assert panel.pages.currentWidget() is panel._sections["reminders"][3]
        assert leaf.unread_reminder  # Opening the panel does not acknowledge.
        checks.append("durable claim precedes system notification submission; bell persists on open")
        page.title.setText("尚未保存的新标题")
        leaf.reminders.reload()
        assert page.title.text() == "尚未保存的新标题"
        QTest.keyClick(page.ack_button, Qt.Key.Key_Return)
        assert not leaf.unread_reminder and not leaf.reminders.unread
        assert leaf.reminders.ledger.load()[0].state == OccurrenceState.ACKNOWLEDGED
        clock.now -= timedelta(minutes=2)
        leaf.reminders.poll()
        clock.now += timedelta(minutes=2)
        leaf.reminders.poll()
        assert len(notifications) <= 1
        checks.append("explicit keyboard acknowledgement persists; rewind cannot replay today's notification")
        page.title.setText("长事项：" + "安排每天复盘与检查" * 8)
        page.time.setTime(QTime(23, 59))
        page.save_button.click()
        assert leaf.reminders.items[0].id == identity
        panel.resize(560, 480)
        pump()
        panel.grab().save(str(out / "reminders-small-long.png"))
        for label, heading, lead, scroll, button in panel._sections.values():
            assert panel.rect().contains(button.mapTo(panel, button.rect().topLeft()))
            assert panel.rect().contains(button.mapTo(panel, button.rect().bottomRight()))
        panel.select_section("texts")
        panel.grab().save(str(out / "texts-small.png"))
        checks.append("same section shell, minimum size and long title keep scrolling + readable controls")
        leaf.reminders.stop()
        leaf.snippets.stop()
        panel.hide()
        leaf.tray.hide()
        leaf._quitting = True
        leaf.close()
    report = {"passed": len(checks), "checks": checks, "nativeDpr": app.primaryScreen().devicePixelRatio(),
              "supportsMessages": QSystemTrayIcon.supportsMessages(),
              "boundary": "Real Windows Qt form and tray notification submission with controlled one-minute clock advance. Input and clock are programmatic; system notification visibility, physical sleep and multi-monitor remain unverified."}
    (out / "reminder-native-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
