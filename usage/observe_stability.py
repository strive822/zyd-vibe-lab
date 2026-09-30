"""Passive long-duration observation of the existing candidate, with no UI input."""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from measure_idle import WindowsMeter
from measure_live import ExistingLeaf
from usage_app.storage import default_data_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--seconds", type=int, default=3600)
    parser.add_argument("--out", type=Path, default=Path("evidence/m6/stability-one-hour.json"))
    args = parser.parse_args()
    target = ExistingLeaf(args.pid)
    meter = WindowsMeter()
    begin = time.monotonic()
    failures, samples = set(), []
    logs = default_data_dir() / "logs"
    seen = set()
    def diagnostic_events():
        rows = []
        for path in logs.glob("events.jsonl*"):
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    item = json.loads(line)
                    identity = (item.get("at"), item.get("event"), item.get("provider"))
                    if identity not in seen:
                        seen.add(identity)
                        rows.append(item.get("event"))
            except (OSError, ValueError):
                continue
        return rows
    diagnostic_events()  # Start boundary excludes historical diagnostics.
    reason = "duration_completed"
    try:
        while True:
            processes = target.owned_processes()
            if args.pid not in processes:
                reason = "target_exited"
                break
            value = meter.sample(args.pid)
            if value is None:
                reason = "target_unavailable"
                break
            idle, condition, ratio = target.idle_condition()
            samples.append({"seconds": round(time.monotonic() - begin, 2), "residentMB": round(value[1] / 1024 ** 2, 3),
                            "privateMB": round(value[2] / 1024 ** 2, 3), "idle": idle})
            failures.update(event for event in diagnostic_events() if event in ("unexpected_error", "storage_failed"))
            elapsed = time.monotonic() - begin
            if elapsed >= args.seconds:
                break
            time.sleep(min(1, args.seconds - elapsed))
    finally:
        meter.close()
    idle_samples = [row for row in samples if row["idle"]]
    quarter = max(1, len(idle_samples) // 4)
    drift = (statistics.mean(row["privateMB"] for row in idle_samples[-quarter:])
             - statistics.mean(row["privateMB"] for row in idle_samples[:quarter])) if idle_samples else None
    manifest = target.image.parent.parent / "build-manifest.json"
    report = {"status": "completed_without_logged_fault" if reason == "duration_completed" and not failures else "needs_review",
              "seconds": round(time.monotonic() - begin, 2), "endReason": reason,
              "candidateHash": json.loads(manifest.read_text(encoding="utf-8"))["candidateHash"],
              "samples": len(samples), "idleSamples": len(idle_samples), "loggedFaultClasses": sorted(failures),
              "peakMainResidentMB": max((row["residentMB"] for row in samples), default=0),
              "idlePrivateFirstToLastQuarterDriftMB": round(drift, 3) if drift is not None else None,
              "boundary": "One-hour passive reference-device observation. No new app/window, input, keys or snippet content. User may interact normally. Main-process memory only; this is not the separate CPU/owned-child idle gate, overnight endurance, physical sleep or clean-Windows validation. User exit ends the observation and is not automatically a defect."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0 if report["status"] == "completed_without_logged_fault" else 1


if __name__ == "__main__":
    raise SystemExit(main())
