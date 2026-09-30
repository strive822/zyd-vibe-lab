"""Explicit configuration backup recovery, preserving the previous original."""
from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from .storage import JsonStore, NewerSchemaError, StorageError


def restore_configuration(data_dir: Path) -> Path | None:
    store = JsonStore(data_dir / "config.json")
    try:
        store.load()
    except NewerSchemaError:
        raise  # Never use an older backup to downgrade an unknown schema.
    except StorageError:
        pass  # Explicit invocation permits recovery of a damaged configuration.
    backup = store.path.with_suffix(".json.bak")
    try:
        JsonStore.decode(backup.read_text(encoding="utf-8"))
        original: Path | None = None
        if store.path.exists():
            original = data_dir / f"config.before-recovery-{uuid4()}.json"
            with original.open("xb") as file:
                file.write(store.path.read_bytes())
                file.flush()
                os.fsync(file.fileno())
        store.recover_backup()
        return original
    except (OSError, UnicodeError) as error:
        raise StorageError("备份恢复失败，原文件已保留；请检查备份格式、权限或文件占用") from error
