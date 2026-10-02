import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from usage_app.models import Account, Provider
from usage_app.parsers import parse_deepseek
from usage_app.storage import JsonStore, NewerSchemaError, SnapshotCache, StorageError, snapshot_data, snapshot_from_data


def test_atomic_save_failure_preserves_original_and_retry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = JsonStore(tmp_path / "config.json")
    store.save({"name": "original"})
    original = store.path.read_bytes()
    replace = os.replace

    def fail_destination(source: object, destination: object) -> None:
        if Path(destination) == store.path:
            raise PermissionError("locked")
        replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_destination)
    with pytest.raises(StorageError):
        store.save({"name": "updated"})
    assert store.path.read_bytes() == original
    assert not list(tmp_path.glob("*.tmp")) and not list(tmp_path.glob(".*.tmp"))
    monkeypatch.setattr(os, "replace", replace)
    store.save({"name": "updated"})
    assert store.load()["name"] == "updated"
    assert json.loads(store.path.with_suffix(".json.bak").read_text())["name"] == "original"


def test_newer_schema_and_corruption_do_not_overwrite(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / "config.json")
    store.path.write_text('{"schemaVersion": 2, "future": true}')
    original = store.path.read_bytes()
    with pytest.raises(NewerSchemaError):
        store.save({})
    assert store.path.read_bytes() == original
    store.path.write_text("broken")
    with pytest.raises(StorageError):
        store.save({})
    assert store.path.read_text() == "broken"


def test_cache_roundtrip_decimal_and_account_isolation(tmp_path: Path, accounts: dict[Provider, Account], now: datetime) -> None:
    account = accounts[Provider.DEEPSEEK]
    snapshot = parse_deepseek({"is_available": True, "balance_infos": [
        {"currency": "CNY", "total_balance": "0.1234567890123456789"}]}, account, now)
    cache = SnapshotCache(tmp_path)
    cache.save(snapshot)
    assert cache.load(account) == snapshot
    assert cache.load(accounts[Provider.CODEX]) is None
    with pytest.raises(StorageError):
        snapshot_from_data(snapshot_data(snapshot), accounts[Provider.CODEX])
    cache.remove(account.id)
    assert cache.load(account) is None


def test_explicit_backup_recovery(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / "config.json")
    store.save({"name": "good"})
    store.save({"name": "newer"})
    store.path.write_text("corrupt")
    store.recover_backup()
    assert store.load()["name"] == "good"


def test_invalid_utf8_and_unserializable_save_preserve_files(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / "config.json")
    store.path.write_bytes(b"\xff\xfe")
    with pytest.raises(StorageError):
        store.load()
    with pytest.raises(StorageError):
        store.save({})
    assert store.path.read_bytes() == b"\xff\xfe"
    store.path.unlink()
    store.save({"name": "original"})
    original = store.path.read_bytes()
    with pytest.raises(StorageError):
        store.save({"unsupported": object()})
    assert store.path.read_bytes() == original
