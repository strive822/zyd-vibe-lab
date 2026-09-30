"""Stable snippet metadata + independent saved UTF-8 files. No process-exit signal."""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from .models import ProviderError
from .parsers import items, object_map
from .storage import JsonStore, StorageError

ICON_IDS = ("copy", "text", "code", "check", "note")
FAVORITE_SLOTS = 4
MAX_TEXT_BYTES = 1024 * 1024


class ContentStatus(StrEnum):
    READY = "ready"
    EMPTY = "empty"
    MISSING = "missing"
    INVALID_ENCODING = "invalid_encoding"
    READ_ERROR = "read_error"
    TOO_LARGE = "too_large"


CONTENT_MESSAGES = {
    ContentStatus.READY: "已读取保存内容",
    ContentStatus.EMPTY: "正文为空，请在记事本保存内容",
    ContentStatus.MISSING: "正文文件已删除或移动",
    ContentStatus.INVALID_ENCODING: "请在记事本另存为 UTF-8",
    ContentStatus.READ_ERROR: "暂时无法读取正文，请重试",
    ContentStatus.TOO_LARGE: "正文超过 1 MB，请缩短后保存",
}


@dataclass(frozen=True, slots=True)
class Snippet:
    id: str
    name: str
    description: str = ""
    icon_id: str = "copy"
    sort_order: int = 0
    favorite_slot: int | None = None

    def __post_init__(self) -> None:
        if str(UUID(self.id)) != self.id:
            raise ValueError("快捷文本 ID 格式不正确，原配置已保留")
        if not self.name.strip() or len(self.name) > 80 or len(self.description) > 240:
            raise ValueError("名称不能为空或超过80字；说明最多240字")
        if any(ord(char) < 32 for char in self.name + self.description):
            raise ValueError("名称和说明请使用单行文字")
        if self.icon_id not in ICON_IDS or isinstance(self.sort_order, bool) or self.sort_order < 0 or self.favorite_slot is not None and (type(self.favorite_slot) is not int or self.favorite_slot not in range(FAVORITE_SLOTS)):
            raise ValueError("无效的图标、顺序或常用位")

    @property
    def relative_path(self) -> str:
        return f"snippets/{self.id}.txt"


@dataclass(frozen=True, slots=True)
class ContentResult:
    snippet_id: str
    status: ContentStatus
    text: str | None
    loaded_at: datetime

    @property
    def message(self) -> str:
        return CONTENT_MESSAGES[self.status]


def snippet_data(snippet: Snippet) -> dict[str, object]:
    return {"id": snippet.id, "name": snippet.name, "description": snippet.description,
            "iconId": snippet.icon_id, "contentPath": snippet.relative_path,
            "sortOrder": snippet.sort_order, "favoriteSlot": snippet.favorite_slot}


class SnippetStore:
    def __init__(self, data_dir: Path):
        self.root = data_dir
        self.store = JsonStore(data_dir / "config.json")

    def load(self) -> tuple[Snippet, ...]:
        data = self.store.load()
        if data is None:
            return ()
        try:
            snippets = []
            identities = set()
            favorites = set()
            for raw in items(data.get("snippets", [])):
                entry = object_map(raw)
                identity, name = entry.get("id"), entry.get("name")
                description, icon = entry.get("description", ""), entry.get("iconId", "copy")
                order, favorite = entry.get("sortOrder", 0), entry.get("favoriteSlot")
                if not all(isinstance(value, str) for value in (identity, name, description, icon)):
                    raise ValueError
                if not isinstance(order, int) or isinstance(order, bool):
                    raise ValueError
                if favorite is not None and (not isinstance(favorite, int) or isinstance(favorite, bool)):
                    raise ValueError
                snippet = Snippet(str(identity), str(name), str(description), str(icon), order, favorite)
                if entry.get("contentPath") != snippet.relative_path or identity in identities or (favorite is not None and favorite in favorites):
                    raise ValueError
                identities.add(identity)
                if favorite is not None:
                    favorites.add(favorite)
                snippets.append(snippet)
            return tuple(sorted(snippets, key=lambda item: (item.sort_order, item.id)))
        except (ValueError, ProviderError) as exc:
            raise StorageError("快捷文本配置损坏；原文件已保留") from exc

    def _save(self, snippets: tuple[Snippet, ...]) -> None:
        data = self.store.load() or {}
        data["snippets"] = [snippet_data(replace(item, sort_order=index)) for index, item in enumerate(snippets)]
        self.store.save(data)

    def path_for(self, snippet: Snippet) -> Path:
        directory = self.root / "snippets"
        path = directory / f"{snippet.id}.txt"
        if directory.is_symlink() or directory.is_junction() or path.is_symlink() or path.is_junction():
            raise StorageError("正文必须是此快捷项的独立本地文件")
        if path.exists() and path.stat().st_nlink > 1:
            raise StorageError("正文不能与另一文件共享硬链接")
        return path

    def add(self, name: str, description: str = "", icon_id: str = "copy", favorite_slot: int | None = None) -> Snippet:
        previous = self.load()
        snippet = Snippet(str(uuid4()), name, description, icon_id, len(previous), favorite_slot)
        path = self.path_for(snippet)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8", newline="") as file:
                file.flush()
                os.fsync(file.fileno())
        except OSError as exc:
            raise StorageError("无法新建正文；配置未修改") from exc
        try:
            retained = tuple(replace(item, favorite_slot=None) if favorite_slot is not None and item.favorite_slot == favorite_slot else item for item in previous)
            self._save((*retained, snippet))
        except StorageError:
            path.unlink(missing_ok=True)
            raise
        return snippet

    def update(self, snippet_id: str, *, name: str, description: str, icon_id: str, favorite_slot: int | None) -> Snippet:
        previous = self.load()
        existing = next((item for item in previous if item.id == snippet_id), None)
        if existing is None:
            raise StorageError("此快捷项已不存在")
        updated = replace(existing, name=name, description=description, icon_id=icon_id, favorite_slot=favorite_slot)
        values = []
        for item in previous:
            if item.id == snippet_id:
                values.append(updated)
            elif favorite_slot is not None and item.favorite_slot == favorite_slot:
                values.append(replace(item, favorite_slot=None))
            else:
                values.append(item)
        self._save(tuple(values))
        return updated

    def reorder(self, identities: tuple[str, ...]) -> None:
        previous = self.load()
        lookup = {item.id: item for item in previous}
        if len(identities) != len(previous) or set(identities) != set(lookup):
            raise StorageError("排序与现有文本不一致，请重新读取")
        self._save(tuple(lookup[identity] for identity in identities))

    def delete(self, snippet_id: str) -> None:
        previous = self.load()
        snippet = next((item for item in previous if item.id == snippet_id), None)
        if snippet is None:
            return
        path = self.path_for(snippet)
        self._save(tuple(item for item in previous if item.id != snippet_id))
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise StorageError("快捷项已移除；正文文件未能删除") from exc

    def read_content(self, snippet_id: str) -> ContentResult:
        snippet = next((item for item in self.load() if item.id == snippet_id), None)
        now = datetime.now(UTC)
        if snippet is None:
            return ContentResult(snippet_id, ContentStatus.MISSING, None, now)
        try:
            path = self.path_for(snippet)
            with path.open("rb") as file:
                raw = file.read(MAX_TEXT_BYTES + 1)
            if len(raw) > MAX_TEXT_BYTES:
                return ContentResult(snippet_id, ContentStatus.TOO_LARGE, None, now)
            text = raw.decode("utf-8-sig")  # Accept a Notepad UTF-8 BOM, preserve newlines/spaces.
            if "\x00" in text:
                return ContentResult(snippet_id, ContentStatus.INVALID_ENCODING, None, now)
            return ContentResult(snippet_id, ContentStatus.READY if text else ContentStatus.EMPTY, text, now)
        except FileNotFoundError:
            return ContentResult(snippet_id, ContentStatus.MISSING, None, now)
        except UnicodeDecodeError:
            return ContentResult(snippet_id, ContentStatus.INVALID_ENCODING, None, now)
        except (OSError, StorageError):
            return ContentResult(snippet_id, ContentStatus.READ_ERROR, None, now)

    def display_name(self, snippet: Snippet) -> str:
        duplicates = sum(item.name == snippet.name for item in self.load()) > 1
        return f"{snippet.name} · {snippet.id[-6:]}" if duplicates else snippet.name
