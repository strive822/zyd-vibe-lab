"""Versioned, atomic, per-user JSON storage. No raw credentials or responses."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from .models import Account, Balance, Provider, ProviderError, QuotaWindow, RecoveryKind, UsageSnapshot
from .parsers import money, object_map, percentage


class StorageError(Exception):
    pass


class NewerSchemaError(StorageError):
    pass


def default_data_dir() -> Path:
    if os.name != "nt":
        raise StorageError("Production data storage requires Windows")
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        raise StorageError("User data directory unavailable")
    return Path(base) / "Duizhaoye"


class JsonStore:
    def __init__(self, path: Path):
        self.path = path

    @staticmethod
    def decode(raw: str) -> dict[str, object]:
        try:
            value = object_map(json.loads(raw))
            version = value.get("schemaVersion")
            if isinstance(version, int) and not isinstance(version, bool) and version > 1:
                raise NewerSchemaError("Newer configuration version; file was preserved")
            if version != 1 or isinstance(version, bool):
                raise StorageError("Unsupported configuration version")
            return value
        except (ValueError, TypeError, ProviderError) as exc:
            raise StorageError("Invalid configuration; file was preserved") from exc

    def load(self) -> dict[str, object] | None:
        try:
            return self.decode(self.path.read_text(encoding="utf-8")) if self.path.exists() else None
        except OSError as exc:
            raise StorageError("Cannot read configuration") from exc
        except UnicodeError as exc:
            raise StorageError("Invalid configuration; file was preserved") from exc

    @staticmethod
    def _stage(directory: Path, content: bytes) -> Path:
        staged: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=directory, prefix=".duizhaoye-", suffix=".tmp", delete=False) as file:
                staged = Path(file.name)
                file.write(content)
                file.flush()
                os.fsync(file.fileno())
            return staged
        except OSError:
            if staged is not None:
                staged.unlink(missing_ok=True)
            raise

    def save(self, value: dict[str, object]) -> None:
        # Read first: a corrupt or newer file cannot be accidentally overwritten.
        self.load()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps({**value, "schemaVersion": 1}, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            raise StorageError("Save failed; previous configuration was preserved") from exc
        staged: Path | None = None
        backup_stage: Path | None = None
        try:
            staged = self._stage(self.path.parent, payload)
            if self.path.exists():
                backup_stage = self._stage(self.path.parent, self.path.read_bytes())
                os.replace(backup_stage, self.path.with_suffix(self.path.suffix + ".bak"))
                backup_stage = None
            os.replace(staged, self.path)
            staged = None
        except OSError as exc:
            raise StorageError("Save failed; previous configuration was preserved") from exc
        finally:
            for temporary in (staged, backup_stage):
                if temporary is not None:
                    temporary.unlink(missing_ok=True)

    def recover_backup(self) -> None:
        backup = self.path.with_suffix(self.path.suffix + ".bak")
        try:
            content = backup.read_text(encoding="utf-8")
            self.decode(content)
            staged = self._stage(self.path.parent, content.encode("utf-8"))
            try:
                os.replace(staged, self.path)
            finally:
                staged.unlink(missing_ok=True)
        except OSError as exc:
            raise StorageError("Recovery failed; files were preserved") from exc
        except UnicodeError as exc:
            raise StorageError("Recovery failed; files were preserved") from exc


def snapshot_data(snapshot: UsageSnapshot) -> dict[str, object]:
    return {
        "accountId": snapshot.account_id, "provider": snapshot.provider.value,
        "sourceKind": snapshot.source_kind, "lastSuccessAt": snapshot.last_success_at.isoformat(),
        "sourceObservedAt": snapshot.source_observed_at.isoformat() if snapshot.source_observed_at else None,
        "windows": [
            {"id": window.id, "sourceBucketId": window.source_bucket_id, "label": window.label,
             "durationMinutes": window.duration_minutes, "remainingPercent": window.remaining_percent,
             "recoveryKind": window.recovery_kind.value,
             "nextRecoveryAt": window.next_recovery_at.isoformat() if window.next_recovery_at else None,
             "usedAmount": str(window.used_amount) if window.used_amount is not None else None,
             "totalAmount": str(window.total_amount) if window.total_amount is not None else None,
             "unit": window.unit} for window in snapshot.windows
        ],
        "balances": [{"currency": balance.currency, "total": str(balance.total),
                      "granted": str(balance.granted) if balance.granted is not None else None,
                      "toppedUp": str(balance.topped_up) if balance.topped_up is not None else None,
                      "isAvailable": balance.is_available} for balance in snapshot.balances],
    }


def snapshot_from_data(value: object, account: Account) -> UsageSnapshot:
    try:
        body = object_map(value)
        if body.get("accountId") != account.id or body.get("provider") != account.provider.value:
            raise ValueError("Account mismatch")
        raw_windows = body.get("windows")
        raw_balances = body.get("balances")
        if not isinstance(raw_windows, list) or not isinstance(raw_balances, list):
            raise ValueError("Invalid snapshot")
        windows = []
        for raw in raw_windows:
            window = object_map(raw)
            duration = window.get("durationMinutes")
            if duration is not None and (not isinstance(duration, int) or isinstance(duration, bool)):
                raise ValueError("Invalid duration")
            windows.append(QuotaWindow(
                str(window["id"]), str(window["sourceBucketId"]), duration,
                percentage(window["remainingPercent"]) if window.get("remainingPercent") is not None else None,
                RecoveryKind(str(window["recoveryKind"])),
                datetime.fromisoformat(str(window["nextRecoveryAt"])) if window.get("nextRecoveryAt") else None,
                money(window["usedAmount"]) if window.get("usedAmount") is not None else None,
                money(window["totalAmount"]) if window.get("totalAmount") is not None else None,
                str(window["unit"]) if window.get("unit") is not None else None, str(window.get("label", "")),
            ))
        balances = []
        for raw in raw_balances:
            balance = object_map(raw)
            available = balance.get("isAvailable")
            if available is not None and not isinstance(available, bool):
                raise ValueError("Invalid availability")
            balances.append(Balance(str(balance["currency"]), money(balance["total"]),
                                    money(balance["granted"]) if balance.get("granted") is not None else None,
                                    money(balance["toppedUp"]) if balance.get("toppedUp") is not None else None, available))
        return UsageSnapshot(account.id, Provider(str(body["provider"])), str(body["sourceKind"]),
                             tuple(windows), tuple(balances), datetime.fromisoformat(str(body["lastSuccessAt"])),
                             datetime.fromisoformat(str(body["sourceObservedAt"])) if body.get("sourceObservedAt") else None)
    except (ValueError, TypeError, KeyError, ProviderError) as exc:
        # ProviderError also becomes a local cache error; no invalid file is accepted.
        raise StorageError("Invalid cached snapshot; file was preserved") from exc


class SnapshotCache:
    def __init__(self, data_dir: Path):
        self.store = JsonStore(data_dir / "snapshots.json")

    def _values(self) -> dict[str, object]:
        previous = self.store.load()
        try:
            return object_map(previous.get("snapshots")) if previous else {}
        except ProviderError as exc:
            raise StorageError("Invalid snapshot cache; file was preserved") from exc

    def load(self, account: Account) -> UsageSnapshot | None:
        snapshots = self._values()
        raw = snapshots.get(account.id)
        return snapshot_from_data(raw, account) if raw is not None else None

    def save(self, snapshot: UsageSnapshot) -> None:
        values = self._values()
        values[snapshot.account_id] = snapshot_data(snapshot)
        self.store.save({"snapshots": values})

    def remove(self, account_id: str) -> None:
        values = self._values()
        values.pop(account_id, None)
        self.store.save({"snapshots": values})
