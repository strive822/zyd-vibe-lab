"""Own process probes for single-instance restore, live locks and crash recovery."""
from __future__ import annotations

from _paths import EVIDENCE

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from usage_app.desktop import SingleInstance
from usage_app.storage import StorageError


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--peer", choices=("restore", "blocked", "crash"))
    parser.add_argument("--data", type=Path)
    args = parser.parse_args()
    _app = QCoreApplication([])  # Keep the application alive for the process.
    if args.peer:
        assert args.data is not None
        instance = SingleInstance(args.data)
        if args.peer == "crash":
            assert instance.acquire()
            os._exit(0)  # Only our temporary lock-owner process; no GUI or user data.
        try:
            assert not instance.acquire()
        except StorageError:
            assert args.peer == "blocked"
            return 0
        assert args.peer == "restore"
        return 0
    checks = []
    def peer(mode: str, data: Path) -> None:
        child = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()),
                                  "--peer", mode, "--data", str(data)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deadline = time.monotonic() + 6
        while child.poll() is None and time.monotonic() < deadline:
            loop = QEventLoop()
            QTimer.singleShot(20, loop.quit)
            loop.exec()
        stdout, stderr = child.communicate(timeout=1)
        assert child.returncode == 0, stderr.decode(errors="replace")
    with tempfile.TemporaryDirectory(prefix="usage-instance-") as directory:
        root = Path(directory)
        first = SingleInstance(root)
        assert first.acquire()
        restored: list[bool] = []
        first.on_restore(lambda: restored.append(True))
        peer("restore", root)
        assert len(restored) == 1
        checks.append("repeat launch acknowledges the existing owner without creating a second runtime")
        old = time.time() - 3600
        os.utime(root / "instance.lock", (old, old))
        peer("restore", root)
        assert len(restored) == 2 and first.lock.isLocked()
        checks.append("a one-hour-old live lock is not stolen by another launch")
        first.server.close()
        peer("blocked", root)
        assert first.lock.isLocked()
        checks.append("an unavailable restore channel never falls through to a duplicate server")
        first.lock.unlock()
        crash = root / "crash"
        peer("crash", crash)
        assert (crash / "instance.lock").exists()
        recovered = SingleInstance(crash)
        assert recovered.acquire()
        recovered.server.close()
        recovered.lock.unlock()
        checks.append("a terminated owner leaves no permanent stale-lock startup failure")
    report = {"passed": len(checks), "checks": checks,
              "boundary": "Real Windows Qt IPC and filesystem locks in owned temporary subprocesses. No user windows, clipboard, credentials or account requests."}
    out = EVIDENCE / "m6/startup-identity-native.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
