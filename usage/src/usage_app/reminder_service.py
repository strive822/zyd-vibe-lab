"""Qt tick/file observation around pure daily scheduling and a durable ledger."""
from __future__ import annotations

import re
import time as monotonic_time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimeZone, QTimer, Signal

from .reminders import Occurrence, Reminder, ReminderLedger, ReminderStore
from .storage import StorageError


@dataclass(frozen=True, slots=True)
class ClockReading:
    now: datetime
    zone: tzinfo
    zone_label: str


class Clock(Protocol):
    def read(self) -> ClockReading: ...


class SystemClock:
    def read(self) -> ClockReading:
        qt_zone = QTimeZone.systemTimeZone()
        if not qt_zone.isValid():
            raise StorageError("无法识别本机时区，提醒已暂停；请检查 Windows 时区设置")
        identity = bytes(qt_zone.id().data()).decode("utf-8")
        try:
            zone: tzinfo = ZoneInfo(identity)
        except (ZoneInfoNotFoundError, ValueError) as error:
            fixed = re.fullmatch(r"UTC([+-])(\d{2}):(\d{2})", identity)
            if not fixed or int(fixed[2]) > 23 or int(fixed[3]) > 59:
                raise StorageError("无法识别本机时区，提醒已暂停；请检查 Windows 时区设置") from error
            offset = timedelta(hours=int(fixed[2]), minutes=int(fixed[3]))
            zone = timezone(offset if fixed[1] == "+" else -offset)
        return ClockReading(datetime.now(UTC), zone, qt_zone.displayName(QTimeZone.TimeType.StandardTime))


class ReminderService(QObject):
    changed = Signal()
    due = Signal(object)
    error = Signal(str)

    def __init__(self, data_dir: Path, parent: QObject | None = None, *, clock: Clock | None = None) -> None:
        super().__init__(parent)
        self.store = ReminderStore(data_dir)
        self.ledger = ReminderLedger(data_dir)
        self.clock = clock or SystemClock()
        self.items: tuple[Reminder, ...] = ()
        self.unread: tuple[Occurrence, ...] = ()
        self.problem: str | None = None
        self._retry_at = 0.0
        self._stopped = False
        self._zone_label: str | None = None
        self._watch = QFileSystemWatcher(self)
        self._reload_timer = QTimer(self)
        self._reload_timer.setSingleShot(True)
        self._reload_timer.timeout.connect(self.reload)
        self._watch.directoryChanged.connect(lambda path: self._reload_timer.start(120))
        self._watch.fileChanged.connect(lambda path: self._reload_timer.start(120))
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.poll)
        self.reload()
        self._timer.start()
        QTimer.singleShot(0, self.poll)

    def _problem(self, error: StorageError) -> None:
        message = str(error)
        if self.problem != message:
            self.problem = message
            self.error.emit(message)
            self.changed.emit()
        self._retry_at = monotonic_time.monotonic() + 30

    def _sync_watches(self) -> None:
        path = str(self.store.store.path)
        if self.store.store.path.exists() and path not in self._watch.files():
            self._watch.addPath(path)
        root = str(self.store.store.path.parent)
        if root not in self._watch.directories():
            self._watch.addPath(root)

    def reload(self) -> None:
        if self._stopped:
            return
        try:
            items, unread = self.store.load(), self.ledger.unread()
            clear_problem = monotonic_time.monotonic() >= self._retry_at
            changed = items != self.items or unread != self.unread or (self.problem is not None and clear_problem)
            self.items, self.unread = items, unread
            if clear_problem:
                self.problem = None
            self._sync_watches()
            if changed:
                self.changed.emit()
        except StorageError as error:
            self._problem(error)

    def poll(self) -> None:
        if self._stopped or monotonic_time.monotonic() < self._retry_at:
            return
        try:
            reading = self.clock.read()
            zone_changed = self._zone_label != reading.zone_label
            self._zone_label = reading.zone_label
            due = self.ledger.claim_due(self.items, reading.now, reading.zone)
            unread = self.ledger.unread()
            recovered = self.problem is not None
            self.problem, self._retry_at = None, 0
            if due:
                self.unread = unread
                self.changed.emit()
                self.due.emit(due)  # Atomic claim has already completed.
            elif self.unread != unread or recovered or zone_changed:
                self.unread = unread
                self.changed.emit()
        except StorageError as error:
            self._problem(error)

    def submitted(self, occurrences: tuple[Occurrence, ...]) -> None:
        try:
            self.ledger.mark_submitted(occurrences, self.clock.read().now)
            self._retry_at = 0
            self.reload()
        except StorageError as error:
            self._problem(error)

    def acknowledge_all(self) -> None:
        try:
            self.ledger.acknowledge({item.key for item in self.unread}, self.clock.read().now)
            self._retry_at = 0
            self.reload()
        except StorageError as error:
            self._problem(error)

    def delete(self, identity: str) -> None:
        self.store.delete(identity)
        keys = {item.key for item in self.ledger.unread() if item.reminder_id == identity}
        if keys:
            self.ledger.acknowledge(keys, self.clock.read().now)
        self.reload()

    def stop(self) -> None:
        self._stopped = True
        self._timer.stop()
        self._reload_timer.stop()
        if self._watch.files():
            self._watch.removePaths(self._watch.files())
        if self._watch.directories():
            self._watch.removePaths(self._watch.directories())
