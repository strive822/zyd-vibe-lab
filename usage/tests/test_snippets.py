from pathlib import Path

import pytest

from usage_app.snippets import ContentStatus, Snippet, SnippetStore
from usage_app.storage import JsonStore, NewerSchemaError, StorageError


def test_case_variants_cannot_alias_another_uuid_file_on_windows():
    with pytest.raises(ValueError):
        Snippet("ABCDEFAB-1234-1234-1234-1234567890AB", "alias")
    with pytest.raises(ValueError):
        Snippet("abcdefab1234123412341234567890ab", "alias")


def test_rename_reorder_and_favorites_keep_identity_and_body(tmp_path: Path):
    store = SnippetStore(tmp_path)
    a, b = store.add("同名"), store.add("同名")
    body = "  中文 English\r\n第二行 😀\n\t末尾  "
    store.path_for(a).write_bytes(body.encode("utf-8"))
    assert store.display_name(a) != store.display_name(b)
    renamed = store.update(a.id, name="已改名", description="说明", icon_id="code", favorite_slot=0)
    assert renamed.id == a.id and store.read_content(a.id).text == body
    store.reorder((b.id, a.id))
    assert store.load()[1].id == a.id
    store.update(b.id, name=b.name, description="", icon_id="text", favorite_slot=0)
    assert store.load()[0].favorite_slot == 0 and store.load()[1].favorite_slot is None
    assert store.read_content(b.id).status == ContentStatus.EMPTY


def test_content_empty_missing_invalid_and_large_are_distinct(tmp_path: Path):
    store = SnippetStore(tmp_path)
    snippet = store.add("文本")
    path = store.path_for(snippet)
    assert store.read_content(snippet.id).status == ContentStatus.EMPTY
    path.write_bytes(b"\xef\xbb\xbf" + "😀\r\n".encode())
    assert store.read_content(snippet.id).text == "😀\r\n"
    path.write_bytes("中文".encode("utf-16"))
    assert store.read_content(snippet.id).status == ContentStatus.INVALID_ENCODING
    path.write_bytes(b"x" * (1024 * 1024 + 1))
    assert store.read_content(snippet.id).status == ContentStatus.TOO_LARGE
    path.unlink()
    assert store.read_content(snippet.id).status == ContentStatus.MISSING


def test_failed_add_or_delete_keeps_saved_data(tmp_path: Path, monkeypatch):
    store = SnippetStore(tmp_path)
    a = store.add("保留")
    store.path_for(a).write_bytes(b"keep")
    original = store.store.path.read_bytes()
    def fail(values):
        raise StorageError("synthetic save failure")
    monkeypatch.setattr(store, "_save", fail)
    with pytest.raises(StorageError):
        store.add("失败")
    assert list((tmp_path / "snippets").glob("*.txt")) == [store.path_for(a)]
    with pytest.raises(StorageError):
        store.delete(a.id)
    assert store.read_content(a.id).text == "keep" and store.store.path.read_bytes() == original


def test_snippet_writes_preserve_other_sections_and_reject_path_traversal(tmp_path: Path):
    config = JsonStore(tmp_path / "config.json")
    config.save({"accounts": [{"unchanged": "synthetic"}], "settings": {"unchanged": True}})
    store = SnippetStore(tmp_path)
    store.add("文本")
    assert config.load()["accounts"] == [{"unchanged": "synthetic"}]
    raw = config.load()
    raw["snippets"][0]["contentPath"] = "../outside.txt"
    config.save(raw)
    with pytest.raises(StorageError):
        store.load()
    config.path.write_text('{"schemaVersion":999}', encoding="utf-8")
    with pytest.raises(NewerSchemaError):
        store.add("不能覆盖新版本")


def test_delete_one_item_preserves_other_body(tmp_path: Path):
    store = SnippetStore(tmp_path)
    a, b = store.add("a"), store.add("b")
    store.path_for(b).write_bytes(b"second body")
    store.delete(a.id)
    assert len(store.load()) == 1 and store.read_content(b.id).text == "second body"


def test_four_favorites_preserve_existing_slots_and_independent_files(tmp_path: Path):
    store = SnippetStore(tmp_path)
    originals = [store.add(f"常用 {index + 1}", favorite_slot=index) for index in range(4)]
    for index, item in enumerate(originals):
        store.path_for(item).write_text(f"正文 {index + 1}", encoding="utf-8")
    replacement = store.add("替换第四位", favorite_slot=3)
    loaded = {item.id: item for item in store.load()}
    assert [loaded[item.id].favorite_slot for item in originals] == [0, 1, 2, None]
    assert loaded[replacement.id].favorite_slot == 3
    assert [store.read_content(item.id).text for item in originals] == [f"正文 {index + 1}" for index in range(4)]
    with pytest.raises(ValueError):
        store.add("第五位不存在", favorite_slot=4)
    with pytest.raises(ValueError):
        store.add("无效类型", favorite_slot=2.0)
