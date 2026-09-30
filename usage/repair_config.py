"""Explicit local backup recovery; no automatic repair or credential changes."""
from __future__ import annotations

import argparse
from pathlib import Path

from usage_app.messages import product_message
from usage_app.recovery import restore_configuration
from usage_app.storage import StorageError, default_data_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="usage：保留当前配置并恢复上次备份")
    parser.add_argument("--restore-backup", action="store_true", required=True)
    parser.add_argument("--data-dir", type=Path)
    args = parser.parse_args()
    try:
        original = restore_configuration(args.data_dir or default_data_dir())
        print("配置备份已恢复。" + (f"原文件副本：{original}" if original else ""))
        print("恢复后请重新启动；若旧密钥引用已清理，需要在账户区重新连接。")
    except StorageError as error:
        print(product_message(error))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
