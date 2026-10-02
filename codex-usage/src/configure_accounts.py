"""Local Windows console enrollment; passwords are not command-line arguments."""

from __future__ import annotations

import argparse
import getpass
from pathlib import Path

from usage_app.accounts import AccountStore
from usage_app.credentials import CredentialError, WindowsCredentialStore
from usage_app.models import Provider
from usage_app.storage import StorageError, default_data_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="usage：本机账户安全配置")
    parser.add_argument("provider", choices=("glm", "deepseek"))
    parser.add_argument("--disconnect", action="store_true")
    parser.add_argument("--data-dir", type=Path)
    args = parser.parse_args()
    store = AccountStore(args.data_dir or default_data_dir(), WindowsCredentialStore())
    try:
        provider = Provider(args.provider)
        if args.disconnect:
            store.disconnect(provider)
            print("此平台已解绑，其他平台未变更。")
        else:
            secret = getpass.getpass("在本机输入 API Key（不会回显，不要发到聊天）：").strip()
            store.connect_key(provider, secret)
            print("密钥已存入 Windows 凭据管理器；配置只保存引用。")
    except (CredentialError, StorageError) as error:
        print(str(error))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
