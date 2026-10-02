from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from usage_app.reminders import OccurrenceState, ReminderLedger, ReminderStore, scheduled_at
from usage_app.storage import JsonStore, NewerSchemaError, StorageError


SHANGHAI = ZoneInfo("Asia/Shanghai")
NEW_YORK = ZoneInfo("America/New_York")


def test_daily_claim_before_notify_survives_restart_and_clock_rewind(tmp_path):
    store = ReminderStore(tmp_path)
    ledger = ReminderLedger(tmp_path)
    created = datetime(2026, 9, 29, 1, tzinfo=UTC)
    a = store.add("每日检查", time(9, 0), created)
    before = datetime(2026, 9, 30, 0, 59, 59, tzinfo=UTC)
    assert ledger.claim_due(store.load(), before, SHANGHAI) == ()
    at = before + timedelta(seconds=1)
    due = ledger.claim_due(store.load(), at, SHANGHAI)
    assert len(due) == 1 and due[0].reminder_id == a.id
    assert ledger.load()[0].state == OccurrenceState.CLAIMED
    restarted = ReminderLedger(tmp_path)
    assert restarted.claim_due(store.load(), at + timedelta(hours=5), SHANGHAI) == ()
    assert restarted.claim_due(store.load(), before, SHANGHAI) == ()
    assert restarted.claim_due(store.load(), at, SHANGHAI) == ()
    assert len(restarted.unread()) == 1
    restarted.mark_submitted(due, at)
    assert restarted.load()[0].state == OccurrenceState.SUBMITTED
    restarted.acknowledge({due[0].key}, at + timedelta(seconds=2))
    assert restarted.unread() == ()
    tomorrow = restarted.claim_due(store.load(), at + timedelta(days=1), SHANGHAI)
    assert len(tomorrow) == 1 and tomorrow[0].local_date == date(2026, 10, 1)


def test_same_day_resume_batches_only_today_and_new_past_time_starts_tomorrow(tmp_path):
    store = ReminderStore(tmp_path)
    ledger = ReminderLedger(tmp_path)
    now = datetime(2026, 9, 30, 8, tzinfo=UTC)
    a = store.add("上午", time(9), now - timedelta(days=3))
    b = store.add("午后", time(14), now - timedelta(days=3))
    store.add("未来", time(17), now - timedelta(days=3))
    c = store.add("刚刚新建的早晨提醒", time(9), now)
    due = ledger.claim_due(store.load(), now, SHANGHAI)
    assert {item.reminder_id for item in due} == {a.id, b.id}
    assert all(item.local_date == date(2026, 9, 30) for item in due)
    assert ledger.claim_due(store.load(), now + timedelta(hours=1), SHANGHAI)[0].title == "未来"
    tomorrow = ledger.claim_due(store.load(), now + timedelta(days=1), SHANGHAI)
    assert c.id in {item.reminder_id for item in tomorrow}


def test_disabled_edit_and_reenabled_do_not_replay_a_claimed_date(tmp_path):
    store = ReminderStore(tmp_path)
    ledger = ReminderLedger(tmp_path)
    now = datetime(2026, 9, 30, 1, tzinfo=UTC)
    a = store.add("原事项", time(9), now - timedelta(days=1), enabled=False)
    assert not ledger.claim_due(store.load(), now, SHANGHAI)
    store.update(a.id, "改名", time(9), True)
    due = ledger.claim_due(store.load(), now, SHANGHAI)
    assert due[0].title == "改名"
    store.update(a.id, "再改名", time(10), True)
    assert ledger.claim_due(store.load(), now + timedelta(hours=1), SHANGHAI) == ()
    assert ledger.unread()[0].title == "改名"
    store.update(a.id, "禁用", time(10), False)
    assert ledger.claim_due(store.load(), now + timedelta(days=1), SHANGHAI) == ()


def test_dst_gap_advances_to_first_valid_minute_and_fold_occurs_once(tmp_path):
    assert scheduled_at(date(2026, 3, 8), time(2, 30), NEW_YORK) == datetime(2026, 3, 8, 7, tzinfo=UTC)
    # 01:30 occurs twice on November 1; the first occurrence is chosen.
    assert scheduled_at(date(2026, 11, 1), time(1, 30), NEW_YORK) == datetime(2026, 11, 1, 5, 30, tzinfo=UTC)
    store = ReminderStore(tmp_path)
    store.add("DST", time(1, 30), datetime(2026, 10, 1, tzinfo=UTC))
    ledger = ReminderLedger(tmp_path)
    assert len(ledger.claim_due(store.load(), datetime(2026, 11, 1, 5, 30, tzinfo=UTC), NEW_YORK)) == 1
    assert not ledger.claim_due(store.load(), datetime(2026, 11, 1, 6, 30, tzinfo=UTC), NEW_YORK)
    assert scheduled_at(date(2011, 12, 30), time(9), ZoneInfo("Pacific/Apia")) is None


def test_timezone_change_keeps_id_local_date_idempotency(tmp_path):
    store = ReminderStore(tmp_path)
    ledger = ReminderLedger(tmp_path)
    now = datetime(2026, 9, 30, 15, tzinfo=UTC)
    store.add("每日", time(9), now - timedelta(days=2))
    assert len(ledger.claim_due(store.load(), now, SHANGHAI)) == 1
    assert ledger.claim_due(store.load(), now, NEW_YORK) == ()
    # The next real local date can legitimately have its own occurrence.
    assert len(ledger.claim_due(store.load(), now + timedelta(days=1), NEW_YORK)) == 1


def test_claim_save_failure_cannot_return_a_due_notification(tmp_path, monkeypatch):
    store = ReminderStore(tmp_path)
    ledger = ReminderLedger(tmp_path)
    now = datetime(2026, 9, 30, 1, tzinfo=UTC)
    store.add("提醒", time(9), now - timedelta(days=1))
    def fail(values):
        raise StorageError("synthetic disk failure")
    monkeypatch.setattr(ledger, "_save", fail)
    with pytest.raises(StorageError):
        ledger.claim_due(store.load(), now, SHANGHAI)
    assert not ledger.store.path.exists()


def test_claimed_but_not_submitted_is_unread_without_crash_replay(tmp_path):
    store = ReminderStore(tmp_path)
    ledger = ReminderLedger(tmp_path)
    now = datetime(2026, 9, 30, 1, tzinfo=UTC)
    store.add("勿扰可能阻止展示", time(9), now - timedelta(days=1))
    assert ledger.claim_due(store.load(), now, SHANGHAI)
    assert not ReminderLedger(tmp_path).claim_due(store.load(), now + timedelta(seconds=2), SHANGHAI)
    assert ledger.unread()[0].state == OccurrenceState.CLAIMED
    # The notification API's submission flag is separate from user acknowledgement.
    ledger.mark_submitted(ledger.unread(), now)
    assert ledger.unread()[0].state == OccurrenceState.SUBMITTED


def test_prune_30_days_and_preserve_other_config_and_newer_schema(tmp_path):
    config = JsonStore(tmp_path / "config.json")
    config.save({"accounts": [{"untouched": True}], "snippets": []})
    store = ReminderStore(tmp_path)
    ledger = ReminderLedger(tmp_path)
    now = datetime(2026, 9, 30, 1, tzinfo=UTC)
    store.add("每日", time(9), now - timedelta(days=40))
    for offset in range(35):
        ledger.claim_due(store.load(), now + timedelta(days=offset), SHANGHAI)
    assert len(ledger.load()) == 30
    assert config.load()["accounts"] == [{"untouched": True}]
    store.delete(store.load()[0].id)
    assert not store.load() and len(ledger.load()) == 30
    ledger.store.path.write_text('{"schemaVersion":999}', encoding="utf-8")
    with pytest.raises(NewerSchemaError):
        ledger.claim_due(store.load(), now, SHANGHAI)


def test_corrupt_ledger_is_not_overwritten_or_treated_as_no_claims(tmp_path):
    ledger = ReminderLedger(tmp_path)
    ledger.store.path.write_text('{"schemaVersion":1,"occurrences":[{}]}', encoding="utf-8")
    original = ledger.store.path.read_bytes()
    with pytest.raises(StorageError):
        ledger.claim_due((), datetime(2026, 9, 30, tzinfo=UTC), SHANGHAI)
    assert ledger.store.path.read_bytes() == original
