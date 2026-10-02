import pytest

from usage_app.recovery import restore_configuration
from usage_app.storage import JsonStore, NewerSchemaError, StorageError


def test_explicit_recovery_retains_damaged_original_and_other_files(tmp_path):
    store = JsonStore(tmp_path / "config.json")
    store.save({"name": "previous"})
    store.save({"name": "latest"})
    store.path.write_bytes(b"\xffdamaged")
    ledger = tmp_path / "reminder-ledger.json"
    ledger.write_bytes(b"untouched ledger")
    preserved = restore_configuration(tmp_path)
    assert preserved.read_bytes() == b"\xffdamaged"
    assert store.load()["name"] == "previous"
    assert ledger.read_bytes() == b"untouched ledger"


def test_newer_schema_and_invalid_backup_cannot_be_replaced(tmp_path):
    store = JsonStore(tmp_path / "config.json")
    store.path.write_text('{"schemaVersion":2}', encoding="utf-8")
    store.path.with_suffix(".json.bak").write_text('{"schemaVersion":1}', encoding="utf-8")
    with pytest.raises(NewerSchemaError):
        restore_configuration(tmp_path)
    assert store.path.read_text() == '{"schemaVersion":2}'
    store.path.write_text("damaged", encoding="utf-8")
    store.path.with_suffix(".json.bak").write_bytes(b"\xffbad")
    with pytest.raises(StorageError):
        restore_configuration(tmp_path)
    assert store.path.read_text() == "damaged"
    assert not list(tmp_path.glob("config.before-recovery*"))
