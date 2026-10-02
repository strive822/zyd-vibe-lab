"""Explicit read-only Codex check and synthetic Windows credential roundtrip.

No keys/account identities/raw error bodies are printed or written to evidence.
"""

from __future__ import annotations

from _paths import EVIDENCE

import argparse
import json
import time
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QCoreApplication, QTimer

from usage_app.adapters import CodexAdapter
from usage_app.credentials import WindowsCredentialStore, new_reference
from usage_app.models import Account, Provider, ProviderError, UsageSnapshot
from usage_app.refresh import RequestTicket
from usage_app.storage import snapshot_data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path(EVIDENCE / "m2/live"))
    parser.add_argument("--codex-executable")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    reference = new_reference(Provider.DEEPSEEK, str(uuid4()))
    secrets = WindowsCredentialStore()
    try:
        secrets.write(reference, "synthetic-roundtrip-only-不是用户密钥")
        matched = secrets.read(reference) == "synthetic-roundtrip-only-不是用户密钥"
    finally:
        secrets.delete(reference)
    deleted = secrets.read(reference) is None
    report: dict[str, object] = {"credentialRoundtrip": matched, "credentialDeleted": deleted}
    app = QCoreApplication([])
    adapter = CodexAdapter(executable=args.codex_executable)
    account = Account("00000000-0000-4000-8000-000000000001", Provider.CODEX, "Codex")
    started = time.monotonic()
    def success(ticket: RequestTicket, snapshot: UsageSnapshot) -> None:
        # Redacted projection from documented fields, not the entire raw response.
        data = snapshot_data(snapshot)
        data["windows"] = [{**window, "sourceBucketId": f"bucket-{index // 2 + 1}",
                            "id": f"bucket-{index // 2 + 1}:{window['label']}"}
                           for index, window in enumerate(data["windows"])]
        (args.out_dir / "codex-snapshot.redacted.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        report.update({"codexRead": "passed", "elapsedSeconds": round(time.monotonic() - started, 3),
                       "windowDurations": [item.duration_minutes for item in snapshot.windows],
                       "remainingPercent": [item.remaining_percent for item in snapshot.windows]})
        app.quit()
    def failure(ticket: RequestTicket, error: ProviderError) -> None:
        report.update({"codexRead": error.code.value, "elapsedSeconds": round(time.monotonic() - started, 3)})
        app.quit()
    adapter.succeeded.connect(success)
    adapter.failed.connect(failure)
    QTimer.singleShot(0, lambda: adapter.read(account, RequestTicket(account.id, 1, 1)))
    app.exec()
    # Drain owned process cleanup; no foreign process is inspected or stopped.
    loop = QCoreApplication.instance()
    for _ in range(5):
        loop.processEvents()
        time.sleep(.02)
    (args.out_dir / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0 if report.get("codexRead") == "passed" and matched and deleted else 1


if __name__ == "__main__":
    raise SystemExit(main())
