from pathlib import Path

import pytest

from usage_app.data_location import prepare_data_directory
from usage_app.storage import JsonStore, StorageError


def old_store(root: Path, *, configured: bool) -> None:
    JsonStore(root / "config.json").save({"accounts": [{"credentialRef": "reference-only" if configured else None}],
                                         "snippets": [{"id": "stable-id", "favoriteSlot": 5}] if configured else []})
    if configured:
        (root / "snippets").mkdir()
        (root / "snippets/stable-id.txt").write_text("独立正文\nsecond line", encoding="utf-8")
        JsonStore(root / "reminder-ledger.json").save({"unread": ["occurrence"]})


def test_virtualized_data_beats_new_empty_explorer_configuration(tmp_path: Path) -> None:
    profile, local = tmp_path, tmp_path / "AppData/Local"
    ordinary, packaged = local / "Duizhaoye", local / "Packages/Codex/LocalCache/Local/Duizhaoye"
    old_store(ordinary, configured=False)
    old_store(packaged, configured=True)
    before = (packaged / "config.json").read_bytes()
    target = prepare_data_directory(profile, local)
    assert target == profile / ".usage" and (target / "config.json").read_bytes() == before
    assert (target / "snippets/stable-id.txt").read_text(encoding="utf-8") == "独立正文\nsecond line"
    assert (target / "reminder-ledger.json").read_bytes() == (packaged / "reminder-ledger.json").read_bytes()
    assert (packaged / "config.json").read_bytes() == before and ordinary.exists()
    assert not list(profile.glob(".usage-import-*"))


def test_existing_store_never_reimported_or_overwritten(tmp_path: Path) -> None:
    local = tmp_path / "AppData/Local"
    old_store(local / "Duizhaoye", configured=True)
    target = tmp_path / ".usage"
    target.mkdir()
    (target / "config.json").write_bytes(b"corrupt or newer")
    assert prepare_data_directory(tmp_path, local) == target
    assert (target / "config.json").read_bytes() == b"corrupt or newer"


def test_conflicting_populated_sources_are_preserved(tmp_path: Path) -> None:
    local = tmp_path / "AppData/Local"
    for root in (local / "Duizhaoye", local / "Packages/Codex/LocalCache/Local/Duizhaoye"):
        old_store(root, configured=True)
    with pytest.raises(StorageError, match="多份"):
        prepare_data_directory(tmp_path, local)
    assert not (tmp_path / ".usage").exists()


def test_failed_copy_cannot_publish_partial_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    local = tmp_path / "AppData/Local"
    old_store(local / "Duizhaoye", configured=True)
    def fail(*args: object, **kwargs: object) -> None:
        raise PermissionError("locked")
    monkeypatch.setattr("usage_app.data_location.shutil.copytree", fail)
    with pytest.raises(StorageError):
        prepare_data_directory(tmp_path, local)
    assert not (tmp_path / ".usage").exists() and not list(tmp_path.glob(".usage-import-*"))
    assert (local / "Duizhaoye/config.json").exists()


def test_new_profile_and_unmanaged_target(tmp_path: Path) -> None:
    assert prepare_data_directory(tmp_path, None) == tmp_path / ".usage"
    (tmp_path / ".usage").mkdir()
    (tmp_path / ".usage/unrelated.txt").write_text("keep")
    with pytest.raises(StorageError, match="缺少配置"):
        prepare_data_directory(tmp_path, None)
    assert (tmp_path / ".usage/unrelated.txt").read_text() == "keep"


def test_concurrent_import_preserves_first_published_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    local = tmp_path / "AppData/Local"
    old_store(local / "Duizhaoye", configured=True)
    from usage_app import data_location
    copy = data_location.shutil.copytree
    def publish_first(*args: object, **kwargs: object) -> object:
        result = copy(*args, **kwargs)
        JsonStore(tmp_path / ".usage/config.json").save({"winner": "first complete import"})
        return result
    monkeypatch.setattr(data_location.shutil, "copytree", publish_first)
    target = prepare_data_directory(tmp_path, local)
    assert JsonStore(target / "config.json").load()["winner"] == "first complete import"
    assert not list(tmp_path.glob(".usage-import-*"))
