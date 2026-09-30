"""Daily wall-clock reminders, saved before notification, keyed by ID + local date."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta, tzinfo
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from uuid import UUID, uuid4

from .models import ProviderError
from .parsers import items, object_map
from .storage import JsonStore, StorageError


def aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Absolute reminder times must have a timezone")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class Reminder:
    id: str
    title: str
    local_time: time
    enabled: bool
    created_at: datetime

    def __post_init__(self) -> None:
        if str(UUID(self.id)) != self.id:
            raise ValueError("Invalid reminder identity")
        if not self.title.strip() or len(self.title) > 80 or any(ord(char) < 32 for char in self.title):
            raise ValueError("事项请填写 1–80 字的单行文字")
        if self.local_time.tzinfo or self.local_time.second or self.local_time.microsecond or not isinstance(self.enabled, bool):
            raise ValueError("每日时间使用本机时区，精确到分钟")
        aware(self.created_at)


class ReminderStore:
    def __init__(self, data_dir: Path):
        self.store = JsonStore(data_dir / "config.json")

    def load(self) -> tuple[Reminder, ...]:
        raw = self.store.load() or {}
        try:
            values = []
            for entry in items(raw.get("reminders", [])):
                body = object_map(entry)
                enabled = body.get("enabled")
                if body.get("timeZonePolicy") != "system" or not isinstance(enabled, bool):
                    raise ValueError
                if not isinstance(body.get("title"), str) or not isinstance(body.get("id"), str):
                    raise ValueError
                local_time = time.fromisoformat(str(body["localTime"]))
                values.append(Reminder(str(body["id"]), str(body["title"]), local_time, enabled, datetime.fromisoformat(str(body["createdAt"]))))
            if len({value.id for value in values}) != len(values):
                raise ValueError
            return tuple(values)
        except (ValueError, KeyError, TypeError, ProviderError) as error:
            raise StorageError("每日提醒配置损坏；原文件已保留") from error

    def _save(self, values: tuple[Reminder, ...]) -> None:
        raw = self.store.load() or {}
        raw["reminders"] = [{"id": item.id, "title": item.title, "localTime": item.local_time.isoformat(timespec="minutes"),
                             "timeZonePolicy": "system", "enabled": item.enabled, "createdAt": aware(item.created_at).isoformat()} for item in values]
        self.store.save(raw)

    def add(self, title: str, local_time: time, now: datetime, *, enabled: bool = True) -> Reminder:
        previous = self.load()
        value = Reminder(str(uuid4()), title, local_time, enabled, aware(now))
        self._save((*previous, value))
        return value

    def update(self, identity: str, title: str, local_time: time, enabled: bool) -> Reminder:
        previous = self.load()
        current = next((value for value in previous if value.id == identity), None)
        if current is None:
            raise StorageError("此提醒已不存在，请重新读取")
        updated = replace(current, title=title, local_time=local_time, enabled=enabled)
        self._save(tuple(updated if item.id == identity else item for item in previous))
        return updated

    def delete(self, identity: str) -> None:
        self._save(tuple(item for item in self.load() if item.id != identity))


@lru_cache(maxsize=512)
def scheduled_at(day: date, local_time: time, zone: tzinfo) -> datetime | None:
    """First fold occurrence; nonexistent wall time advances to a valid minute.

    Roundtrip UTC -> zone is the validity check. ZoneInfo attaching tzinfo alone
    does not reject a nonexistent time. A wholly skipped local date has no event.
    """
    wall = datetime.combine(day, local_time)
    while wall.date() == day:
        valid = []
        for fold in (0, 1):
            instant = wall.replace(tzinfo=zone, fold=fold).astimezone(UTC)
            if instant.astimezone(zone).replace(tzinfo=None) == wall:
                valid.append(instant)
        if valid:
            return min(valid)
        wall += timedelta(minutes=1)
    return None


class OccurrenceState(StrEnum):
    CLAIMED = "claimed"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"


@dataclass(frozen=True, slots=True)
class Occurrence:
    reminder_id: str
    local_date: date
    title: str
    scheduled_at: datetime
    state: OccurrenceState
    claimed_at: datetime
    delivered_at: datetime | None = None  # System submission, never proof of being seen.
    acknowledged_at: datetime | None = None

    @property
    def key(self) -> tuple[str, date]:
        return self.reminder_id, self.local_date

    def __post_init__(self) -> None:
        UUID(self.reminder_id)
        aware(self.scheduled_at)
        aware(self.claimed_at)
        if self.delivered_at:
            aware(self.delivered_at)
        if self.acknowledged_at:
            aware(self.acknowledged_at)
        if not self.title.strip() or len(self.title) > 80:
            raise ValueError("Invalid occurrence title")
        if self.state == OccurrenceState.SUBMITTED and self.delivered_at is None:
            raise ValueError("Submitted occurrence needs a submission timestamp")
        if self.state == OccurrenceState.ACKNOWLEDGED and self.acknowledged_at is None:
            raise ValueError("Acknowledged occurrence needs an acknowledgement timestamp")


class ReminderLedger:
    def __init__(self, data_dir: Path):
        self.store = JsonStore(data_dir / "reminder-ledger.json")

    def load(self) -> tuple[Occurrence, ...]:
        raw = self.store.load() or {}
        try:
            values = []
            for entry in items(raw.get("occurrences", [])):
                body = object_map(entry)
                values.append(Occurrence(str(body["reminderId"]), date.fromisoformat(str(body["localDate"])), str(body["title"]),
                                         datetime.fromisoformat(str(body["scheduledAt"])), OccurrenceState(str(body["state"])),
                                         datetime.fromisoformat(str(body["claimedAt"])),
                                         datetime.fromisoformat(str(body["deliveredAt"])) if body.get("deliveredAt") else None,
                                         datetime.fromisoformat(str(body["acknowledgedAt"])) if body.get("acknowledgedAt") else None))
            if len({item.key for item in values}) != len(values):
                raise ValueError
            return tuple(values)
        except (KeyError, ValueError, TypeError, ProviderError) as error:
            raise StorageError("提醒记录损坏；已暂停通知以避免重复，原文件已保留") from error

    def _save(self, values: tuple[Occurrence, ...]) -> None:
        self.store.save({"occurrences": [{"reminderId": item.reminder_id, "localDate": item.local_date.isoformat(), "title": item.title,
                                         "scheduledAt": aware(item.scheduled_at).isoformat(), "state": item.state.value,
                                         "claimedAt": aware(item.claimed_at).isoformat(),
                                         "deliveredAt": aware(item.delivered_at).isoformat() if item.delivered_at else None,
                                         "acknowledgedAt": aware(item.acknowledged_at).isoformat() if item.acknowledged_at else None} for item in values]})

    def claim_due(self, reminders: tuple[Reminder, ...], now: datetime, zone: tzinfo) -> tuple[Occurrence, ...]:
        now = aware(now)
        day = now.astimezone(zone).date()
        previous = self.load()
        claimed = {item.key for item in previous}
        due = []
        for reminder in reminders:
            at = scheduled_at(day, reminder.local_time, zone) if reminder.enabled else None
            if at and reminder.created_at <= at <= now and (reminder.id, day) not in claimed:
                due.append(Occurrence(reminder.id, day, reminder.title, at, OccurrenceState.CLAIMED, now))
        # Keep 30 recent local dates. Future dates from a clock rewind are retained
        # so rewinding and then restoring the clock cannot repeat their events.
        kept = tuple(item for item in previous if item.local_date >= day - timedelta(days=29))
        if due or kept != previous:
            self._save((*kept, *due))  # No notification can precede this commit.
        return tuple(sorted(due, key=lambda item: (item.scheduled_at, item.reminder_id)))

    def mark_submitted(self, occurrences: tuple[Occurrence, ...], now: datetime) -> None:
        keys = {item.key for item in occurrences}
        values = tuple(replace(item, state=OccurrenceState.SUBMITTED, delivered_at=aware(now))
                       if item.key in keys and item.state == OccurrenceState.CLAIMED else item for item in self.load())
        self._save(values)

    def acknowledge(self, keys: set[tuple[str, date]], now: datetime) -> None:
        values = tuple(replace(item, state=OccurrenceState.ACKNOWLEDGED, acknowledged_at=aware(now)) if item.key in keys else item for item in self.load())
        self._save(values)

    def unread(self) -> tuple[Occurrence, ...]:
        return tuple(item for item in self.load() if item.state != OccurrenceState.ACKNOWLEDGED)
