from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from PySide6.QtCore import QCoreApplication

from usage_app.reminder_service import ClockReading, ReminderService
from usage_app.reminders import OccurrenceState, ReminderStore
from usage_app.storage import StorageError


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 9, 30, 1, tzinfo=UTC)

    def read(self):
        return ClockReading(self.now, ZoneInfo("Asia/Shanghai"), "中国标准时间")


@pytest.fixture(scope="module")
def qt_app():
    return QCoreApplication.instance() or QCoreApplication([])


@pytest.fixture
def reminder_service(qt_app, tmp_path):
    clock = FakeClock()
    ReminderStore(tmp_path).add("检查", time(9), clock.now - timedelta(days=1))
    value = ReminderService(tmp_path, clock=clock)
    yield value, clock
    value.stop()


def test_due_signal_observes_committed_claim_then_submission_and_ack(reminder_service):
    value, _ = reminder_service
    due = []
    def notified(batch):
        assert value.ledger.load()[0].state == OccurrenceState.CLAIMED
        due.extend(batch)
    value.due.connect(notified)
    value.poll()
    assert len(due) == 1 and len(value.unread) == 1
    value.poll()
    assert len(due) == 1
    value.submitted(tuple(due))
    assert value.unread[0].state == OccurrenceState.SUBMITTED
    value.acknowledge_all()
    assert value.unread == ()


def test_failed_claim_backs_off_even_when_directory_watch_reload_runs(reminder_service, monkeypatch):
    value, _ = reminder_service
    calls, due = [], []
    original = value.ledger._save
    def fail(entries):
        calls.append(True)
        raise StorageError("synthetic failure")
    value.due.connect(due.extend)
    monkeypatch.setattr(value.ledger, "_save", fail)
    value.poll()
    value.reload()  # Own staged-file changes can cause this path.
    value.poll()
    assert len(calls) == 1 and due == [] and value.problem == "synthetic failure"
    monkeypatch.setattr(value.ledger, "_save", original)
    value._retry_at = 0
    value.poll()
    assert len(due) == 1 and value.problem is None


def test_stop_prevents_due_callback_from_queued_startup(reminder_service, qt_app):
    value, _ = reminder_service
    due = []
    value.due.connect(due.extend)
    value.stop()
    qt_app.processEvents()
    value.poll()
    assert due == [] and not value.ledger.store.path.exists()


def test_unread_reload_after_restart_does_not_replay_notification(reminder_service):
    value, clock = reminder_service
    value.poll()
    value.stop()
    restarted = ReminderService(value.store.store.path.parent, clock=clock)
    due = []
    restarted.due.connect(due.extend)
    try:
        restarted.poll()
        assert not due and len(restarted.unread) == 1
    finally:
        restarted.stop()


def test_timezone_change_updates_explanation_without_replaying_due(reminder_service):
    value, clock = reminder_service
    value.poll()
    changed, due = [], []
    value.changed.connect(lambda: changed.append(True))
    value.due.connect(due.extend)
    clock.read = lambda: ClockReading(clock.now, ZoneInfo("UTC"), "协调世界时")
    value.poll()
    assert changed == [True] and due == [] and value._zone_label == "协调世界时"
