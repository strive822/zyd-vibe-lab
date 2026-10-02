"""Explicit local-key readonly checks. Evidence is a whitelist, never a raw body."""
from __future__ import annotations

from _paths import EVIDENCE

import argparse
import json
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QTimer

from usage_app.accounts import AccountStore
from usage_app.adapters import HttpQuotaAdapter
from usage_app.credentials import WindowsCredentialStore
from usage_app.models import Provider, ProviderError, UsageSnapshot
from usage_app.refresh import RequestTicket
from usage_app.storage import default_data_dir, snapshot_data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", choices=("glm", "deepseek"))
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path(EVIDENCE / "m2/live"))
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    provider = Provider(args.provider)
    secrets = WindowsCredentialStore()
    account = next((item for item in AccountStore(args.data_dir or default_data_dir(), secrets).load()
                    if item.provider == provider and item.enabled and item.credential_ref), None)
    if account is None:
        print(json.dumps({"provider": provider.value, "status": "unconfigured"}))
        return 2
    app = QCoreApplication([])
    adapter = HttpQuotaAdapter(provider, secrets)
    result: dict[str, object] = {"provider": provider.value}
    def observed(value: dict[str, object]) -> None:
        (args.out_dir / "glm-schema.redacted.json").write_text(json.dumps(value, indent=2), encoding="utf-8")
        result["schemaObserved"] = True
    def success(ticket: RequestTicket, snapshot: UsageSnapshot) -> None:
        redacted = replace(snapshot, account_id="00000000-0000-4000-8000-000000000001")
        (args.out_dir / f"{provider.value}-snapshot.redacted.json").write_text(json.dumps(snapshot_data(redacted), indent=2), encoding="utf-8")
        result["status"] = "passed"
        app.quit()
    def failed(ticket: RequestTicket, error: ProviderError) -> None:
        result["status"] = error.code.value
        app.quit()
    adapter.schema_observed.connect(observed)
    adapter.succeeded.connect(success)
    adapter.failed.connect(failed)
    QTimer.singleShot(0, lambda: adapter.read(account, RequestTicket(account.id, 1, 1)))
    app.exec()
    (args.out_dir / f"{provider.value}-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
