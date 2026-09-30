"""Saved-file observation, explicit Notepad launch and verified copy use cases."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QProcess, QTimer, Signal

from .clipboard import ClipboardError, ClipboardWriter, WindowsClipboard
from .messages import product_message
from .snippets import ContentResult, ContentStatus, Snippet, SnippetStore
from .storage import StorageError


@dataclass(frozen=True, slots=True)
class CopyResult:
    snippet_id: str
    name: str
    succeeded: bool
    message: str


class SnippetService(QObject):
    changed = Signal()
    content_changed = Signal(str)
    error = Signal(str)
    copied = Signal(object)

    def __init__(self, data_dir: Path, parent: QObject | None = None, *, clipboard: ClipboardWriter | None = None) -> None:
        super().__init__(parent)
        self.store = SnippetStore(data_dir)
        self.clipboard = clipboard or WindowsClipboard()
        self.items: tuple[Snippet, ...] = ()
        self.problem: str | None = None
        self._stopped = False
        self.latest_content: dict[str, ContentResult] = {}  # Only entries explicitly previewed/copied.
        self._watch = QFileSystemWatcher(self)
        self._reload_timer = QTimer(self)
        self._reload_timer.setSingleShot(True)
        self._reload_timer.timeout.connect(self.reload)
        self._body_timer = QTimer(self)
        self._body_timer.setSingleShot(True)
        self._body_timer.timeout.connect(self._changed_files)
        self._dirty: set[str] = set()
        self._watch.fileChanged.connect(self._file_changed)
        self._watch.directoryChanged.connect(self._directory_changed)
        try:
            (data_dir / "snippets").mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise StorageError("无法打开快捷文本目录，请检查本机文件权限") from error
        self.reload()
        QTimer.singleShot(0, self.reload)  # Reconcile changes during native watcher registration.

    def reload(self) -> None:
        if self._stopped:
            return
        try:
            previous = self.items
            previous_problem = self.problem
            self.items = self.store.load()
            self.latest_content = {key: value for key, value in self.latest_content.items() if any(item.id == key for item in self.items)}
            self._sync_watches()
            self.problem = None
            if previous != self.items or previous_problem is not None:
                self.changed.emit()
        except StorageError as error:
            self.problem = product_message(error)
            self._sync_config_watch()
            self.error.emit(self.problem)

    def _sync_config_watch(self) -> None:
        path, root = str(self.store.store.path), str(self.store.root)
        if self.store.store.path.exists() and path not in self._watch.files():
            self._watch.addPath(path)
        if self.store.root.exists() and root not in self._watch.directories():
            self._watch.addPath(root)

    def _sync_watches(self) -> None:
        paths = [str(self.store.store.path)] if self.store.store.path.exists() else []
        paths += [str(self.store.path_for(item)) for item in self.items if self.store.path_for(item).exists()]
        directories = [str(self.store.root / "snippets"), str(self.store.root)]
        old = set(self._watch.files())
        remove = old - set(paths)
        if remove:
            self._watch.removePaths(list(remove))
        if set(paths) - old:
            self._watch.addPaths(list(set(paths) - old))
        new_directories = [path for path in directories if path not in self._watch.directories()]
        if new_directories:
            self._watch.addPaths(new_directories)

    def _file_changed(self, path: str) -> None:
        if self._stopped:
            return
        if path == str(self.store.store.path):
            self._reload_timer.start(100)
            return
        for item in self.items:
            if path == str(self.store.root / item.relative_path):
                self._dirty.add(item.id)
        self._body_timer.start(150)

    def _directory_changed(self, path: str) -> None:
        if self._stopped:
            return
        if path == str(self.store.root / "snippets"):
            self._dirty.update(item.id for item in self.items)
            self._body_timer.start(150)
        if str(self.store.store.path) not in self._watch.files():
            self._reload_timer.start(100)

    def _changed_files(self) -> None:
        if self._stopped:
            return
        dirty, self._dirty = self._dirty, set()
        for identity in dirty:
            self.latest_content.pop(identity, None)  # Never silently copy a removed file's old cache.
            self.content_changed.emit(identity)
        try:
            self._sync_watches()
        except StorageError as error:
            self.error.emit(product_message(error))

    def favorite(self, slot: int) -> Snippet | None:
        return next((item for item in self.items if item.favorite_slot == slot), None)

    def display_name(self, snippet: Snippet) -> str:
        repeated = sum(item.name == snippet.name for item in self.items) > 1
        return f"{snippet.name} · {snippet.id[-6:]}" if repeated else snippet.name

    def read(self, snippet_id: str) -> ContentResult:
        try:
            result = self.store.read_content(snippet_id)
        except StorageError as error:
            self.error.emit(product_message(error))
            result = ContentResult(snippet_id, ContentStatus.READ_ERROR, None, datetime.now(UTC))
        self.latest_content[snippet_id] = replace(result, text=None)  # No accumulating plaintext body cache.
        return result

    def copy(self, snippet_id: str, owner: int) -> CopyResult:
        snippet = next((item for item in self.items if item.id == snippet_id), None)
        if snippet is None:
            result = CopyResult(snippet_id, "", False, "此快捷项已不存在")
        else:
            body = self.read(snippet_id)
            if body.status != ContentStatus.READY or body.text is None:
                result = CopyResult(snippet_id, snippet.name, False, body.message)
            else:
                try:
                    self.clipboard.write(owner, body.text)
                    result = CopyResult(snippet_id, snippet.name, True, "已写入剪贴板")
                except ClipboardError as error:
                    result = CopyResult(snippet_id, snippet.name, False, str(error))
        self.copied.emit(result)
        return result

    def edit_in_notepad(self, snippet_id: str) -> None:
        snippet = next((item for item in self.items if item.id == snippet_id), None)
        if snippet is None:
            raise StorageError("此快捷项已不存在")
        path = self.store.path_for(snippet)
        if not path.exists():
            raise StorageError("正文已移动或删除，请先恢复文件")
        started, _pid = QProcess.startDetached("notepad.exe", [str(path.resolve())])
        if not started:
            raise StorageError("无法打开系统记事本，请稍后重试")
        # The PID is deliberately unused. Modern Notepad can reuse an existing
        # process and keep tabs open after Ctrl+S; only saved-file events count.

    def stop(self) -> None:
        self._stopped = True
        self._reload_timer.stop()
        self._body_timer.stop()
        if self._watch.files():
            self._watch.removePaths(self._watch.files())
        if self._watch.directories():
            self._watch.removePaths(self._watch.directories())
