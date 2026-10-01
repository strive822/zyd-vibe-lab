"""One physical per-user store, independent of a parent's AppData virtualization."""
from __future__ import annotations

import ctypes
import os
import shutil
import tempfile
from pathlib import Path

from .storage import JsonStore, StorageError


def physical_root(config: Path) -> Path:
    if os.name != "nt":
        return config.resolve().parent
    import msvcrt
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    kernel.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    # Open for reading: metadata-only Path.resolve can miss AppData redirection.
    with config.open("rb") as file:
        buffer = ctypes.create_unicode_buffer(32768)
        size = kernel.GetFinalPathNameByHandleW(msvcrt.get_osfhandle(file.fileno()), buffer, len(buffer), 0)
        if not size or size >= len(buffer):
            raise StorageError("无法确认旧配置的实际目录，原数据已保留。")
    value = buffer.value
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return Path(value).parent


def legacy_sources(local: Path) -> tuple[Path, ...]:
    candidates = [local / "Duizhaoye" / "config.json"]
    candidates.extend((local / "Packages").glob("*/LocalCache/Local/Duizhaoye/config.json"))
    roots: dict[str, Path] = {}
    for config in candidates:
        if config.exists():
            root = physical_root(config)
            roots[str(root).casefold()] = root
    return tuple(roots.values())


def choose_legacy_source(roots: tuple[Path, ...]) -> Path | None:
    populated = []
    for root in roots:
        value = JsonStore(root / "config.json").load()
        if value is None:
            continue
        accounts = value.get("accounts", [])
        has_key = isinstance(accounts, list) and any(isinstance(item, dict) and item.get("credentialRef") for item in accounts)
        cache = JsonStore(root / "snapshots.json").load() if (root / "snapshots.json").exists() else None
        if value.get("snippets") or value.get("reminders") or has_key or cache and cache.get("snapshots"):
            populated.append(root)
    if len(populated) > 1:
        raise StorageError("发现多份已有 usage 数据，未自动合并。请用 --data-dir 指定需要保留的目录。")
    return populated[0] if populated else roots[0] if roots else None


def prepare_data_directory(profile: Path, local: Path | None) -> Path:
    target = profile / ".usage"
    if target.is_symlink() or target.is_junction():
        raise StorageError("usage 数据目录不能是链接，原数据已保留。")
    if (target / "config.json").exists():
        return target  # Existing/corrupt/newer data remains authoritative; never re-import.
    try:
        if target.exists() and any(target.iterdir()):
            raise StorageError("usage 数据目录已有文件但缺少配置，未覆盖现有文件。")
        source = choose_legacy_source(legacy_sources(local)) if local else None
        if source is None:
            return target
        # Publish only a complete copy; original data and Windows credentials stay intact.
        stage = Path(tempfile.mkdtemp(prefix=".usage-import-", dir=profile))
        try:
            for name in ("config.json", "config.json.bak", "snapshots.json", "snapshots.json.bak",
                         "reminder-ledger.json", "reminder-ledger.json.bak", "snippets"):
                path = source / name
                if not path.exists():
                    continue
                if path.is_symlink() or path.is_junction() or path.is_dir() and any(
                    item.is_symlink() or item.is_junction() for item in path.rglob("*")
                ):
                    raise StorageError("旧数据包含链接，未迁移或覆盖正文。")
                if path.is_dir():
                    shutil.copytree(path, stage / name)
                else:
                    shutil.copy2(path, stage / name)
            if (target / "config.json").exists():
                return target  # Another first launch already imported a complete store.
            if target.exists():
                target.rmdir()  # Empty directory only; concurrent writes prevent removal.
            try:
                stage.rename(target)
            except OSError:
                if not (target / "config.json").exists():
                    raise
                # A concurrent first launch already published its complete store.
        finally:
            if stage.exists():
                shutil.rmtree(stage)
        return target
    except OSError as error:
        raise StorageError("数据目录迁移未完成，原配置与正文已保留。") from error
