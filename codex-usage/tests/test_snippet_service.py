import os
from pathlib import Path
from time import monotonic

import pytest
from PySide6.QtCore import QCoreApplication, QEventLoop, QProcess, QTimer

from usage_app.clipboard import ClipboardError, windows_text
from usage_app.snippet_service import SnippetService
from usage_app.snippets import ContentStatus
from usage_app.storage import JsonStore, StorageError


@pytest.fixture(scope="module")
def qt_app():
    return QCoreApplication.instance() or QCoreApplication([])


def until(predicate, timeout=2500):
    loop = QEventLoop()
    poll = QTimer(loop)
    poll.timeout.connect(lambda: loop.quit() if predicate() else None)
    poll.start(10)
    QTimer.singleShot(timeout, loop.quit)
    if not predicate():
        loop.exec()
    poll.stop()
    assert predicate(), "Saved file notification did not arrive"


def replace_saved_file(source: Path, destination: Path, timeout=2500):
    # An external editor may need to wait for a short-lived Windows file handle.
    # Retry only those access/share conflicts; keep persistent failures visible.
    deadline = monotonic() + timeout / 1000
    while True:
        try:
            os.replace(source, destination)
            return
        except PermissionError as error:
            if getattr(error, "winerror", None) not in (5, 32, 33) or monotonic() >= deadline:
                raise
            loop = QEventLoop()
            QTimer.singleShot(10, loop.quit)
            loop.exec()  # Keep native watcher events flowing during the wait.


@pytest.mark.parametrize("winerror", [5, 32, 33])
def test_atomic_save_waits_for_transient_windows_access_conflicts(qt_app, tmp_path, monkeypatch, winerror):
    source, destination = tmp_path / "body.new", tmp_path / "body.txt"
    source.write_bytes(b"saved")
    destination.write_bytes(b"previous")
    replace = os.replace
    calls = []

    def briefly_occupied(old, new):
        calls.append((old, new))
        if len(calls) == 1:
            error = PermissionError("temporary Windows file handle")
            error.winerror = winerror
            raise error
        replace(old, new)

    monkeypatch.setattr(os, "replace", briefly_occupied)
    replace_saved_file(source, destination)
    assert len(calls) == 2 and not source.exists()
    assert destination.read_bytes() == b"saved"


@pytest.mark.parametrize("winerror", [None, 112])
def test_atomic_save_does_not_retry_unrelated_permission_failures(tmp_path, monkeypatch, winerror):
    calls = []
    error = PermissionError("permanent file failure")
    if winerror is not None:
        error.winerror = winerror

    def denied(old, new):
        calls.append((old, new))
        raise error

    monkeypatch.setattr(os, "replace", denied)
    with pytest.raises(PermissionError) as caught:
        replace_saved_file(tmp_path / "body.new", tmp_path / "body.txt")
    assert caught.value is error and len(calls) == 1


def test_atomic_save_reports_persistent_windows_access_conflict(qt_app, tmp_path, monkeypatch):
    source, destination = tmp_path / "body.new", tmp_path / "body.txt"
    source.write_bytes(b"saved")
    destination.write_bytes(b"previous")
    error = PermissionError("persistent Windows file handle")
    error.winerror = 5
    calls = []
    times = iter([0.0, 0.01, 3.0])

    def denied(old, new):
        calls.append((old, new))
        raise error

    monkeypatch.setattr(os, "replace", denied)
    monkeypatch.setattr(__name__ + ".monotonic", lambda: next(times))
    monkeypatch.setattr(QEventLoop, "exec", lambda self: None)
    with pytest.raises(PermissionError) as caught:
        replace_saved_file(source, destination)
    assert caught.value is error and len(calls) == 2
    assert source.read_bytes() == b"saved" and destination.read_bytes() == b"previous"


class Writer:
    def __init__(self):
        self.calls = []
        self.busy = False

    def write(self, owner, text):
        if self.busy:
            raise ClipboardError("剪贴板暂时被占用，请重试")
        self.calls.append((owner, text))


@pytest.fixture
def service(qt_app, tmp_path):
    writer = Writer()
    value = SnippetService(tmp_path, clipboard=writer)
    yield value, writer
    value.stop()


def test_copy_uses_only_saved_body_and_reports_native_failure(service):
    value, writer = service
    a = value.store.add("a", favorite_slot=0)
    b = value.store.add("b", favorite_slot=1)
    value.reload()
    assert not value.copy(a.id, 7).succeeded and not writer.calls
    body = "  中文 😀 e\u0301\r\n\t第二行  \n"
    value.store.path_for(a).write_bytes(body.encode())
    assert value.copy(a.id, 7).succeeded
    assert writer.calls == [(7, body)]
    assert value.latest_content[a.id].text is None
    writer.busy = True
    assert not value.copy(a.id, 7).succeeded and len(writer.calls) == 1
    value.store.path_for(a).unlink()
    writer.busy = False
    assert not value.copy(a.id, 7).succeeded and len(writer.calls) == 1
    assert not value.copy(b.id, 7).succeeded
    assert not value.copy("removed", 7).succeeded
    assert windows_text(body) == "  中文 😀 e\u0301\r\n\t第二行  \r\n"


def test_watcher_rearms_after_atomic_save_delete_and_recreation(service):
    value, writer = service
    a, b = value.store.add("a"), value.store.add("b")
    value.store.path_for(b).write_bytes(b"second")
    value.reload()
    observed = []
    value.content_changed.connect(observed.append)
    path = value.store.path_for(a)
    path.write_bytes("首次保存".encode())
    until(lambda: a.id in observed)
    assert value.read(a.id).text == "首次保存"
    for text in ("原子保存一", "原子保存二"):
        observed.clear()
        temporary = path.with_suffix(".new")
        temporary.write_bytes(text.encode())
        replace_saved_file(temporary, path)
        observed.clear()  # Ignore directory events from creating the temporary file.
        until(lambda: a.id in observed)
        assert value.read(a.id).text == text
    observed.clear()
    path.unlink()
    until(lambda: a.id in observed)
    assert value.read(a.id).status == ContentStatus.MISSING
    observed.clear()
    path.write_bytes(b"recreated")
    until(lambda: a.id in observed)
    assert value.copy(a.id, 7).succeeded and writer.calls[-1] == (7, "recreated")
    assert value.read(b.id).text == "second"


def test_unrelated_config_save_does_not_reload_form_metadata(service):
    value, _ = service
    value.store.add("a")
    value.reload()
    changed = []
    value.changed.connect(lambda: changed.append(True))
    config = JsonStore(value.store.root / "config.json")
    raw = config.load()
    raw["settings"] = {"test": True}
    config.save(raw)
    value.reload()
    assert changed == []


def test_notepad_arguments_are_independent_paths_and_exit_is_unused(service, monkeypatch):
    value, _ = service
    a, b = value.store.add("同名"), value.store.add("同名")
    value.reload()
    launches = []
    monkeypatch.setattr(QProcess, "startDetached", lambda executable, arguments: (launches.append((executable, arguments)) or True, 123))
    value.edit_in_notepad(a.id)
    value.edit_in_notepad(b.id)
    assert all(exe == "notepad.exe" for exe, _ in launches)
    assert launches[0][1] != launches[1][1]
    assert value.read(a.id).status == ContentStatus.EMPTY
    monkeypatch.setattr(QProcess, "startDetached", lambda executable, arguments: (False, 0))
    with pytest.raises(StorageError, match="无法打开"):
        value.edit_in_notepad(a.id)


def test_external_link_cannot_redirect_an_independent_body(service, tmp_path: Path):
    value, _ = service
    a, b = value.store.add("a"), value.store.add("b")
    path = value.store.path_for(a)
    target = value.store.path_for(b)
    target.write_bytes(b"other body")
    path.unlink()
    os.link(target, path)
    assert value.read(a.id).status == ContentStatus.READ_ERROR
    assert not value.copy(a.id, 7).succeeded


def test_initial_config_error_remains_visible_and_repair_is_observed(qt_app, tmp_path):
    config = tmp_path / "config.json"
    config.write_bytes(b"broken")
    value = SnippetService(tmp_path, clipboard=Writer())
    try:
        assert value.problem and "配置损坏" in value.problem
        assert str(config) in value._watch.files()
        config.write_text('{"schemaVersion":1,"snippets":[]}', encoding="utf-8")
        until(lambda: value.problem is None)
        assert value.items == ()
    finally:
        value.stop()
