"""Qt text-bound checks for live-data slots, with synthetic domain scenarios.

Scaling is rendering simulation; this never claims physical mixed-DPI coverage.
"""
from __future__ import annotations

from _paths import EVIDENCE

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1)
    parser.add_argument("--expected-dpr", type=float, default=1.5)
    parser.add_argument("--out-dir", type=Path, default=Path(EVIDENCE / "m2/layout/150"))
    args = parser.parse_args()
    os.environ["QT_SCALE_FACTOR"] = str(args.scale)
    from PySide6.QtWidgets import QApplication
    from usage_app.models import Balance, ErrorCode, Provider, QuotaWindow, RecoveryKind, Status, UsageSnapshot
    from usage_app.runtime import UsageRuntime
    from usage_app.widget import LiveLeaf

    app = QApplication([])
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = {"actualDpr": app.primaryScreen().devicePixelRatio(), "cases": 0, "issues": []}
    if abs(report["actualDpr"] - args.expected_dpr) > .015:
        raise ValueError("Actual DPR did not match the requested check")
    now = datetime(2026, 9, 30, 3, 59, tzinfo=UTC)
    with tempfile.TemporaryDirectory(prefix="duizhaoye-m2-audit-") as root:
        runtime = UsageRuntime(Path(root))
        runtime.stop()
        states = runtime.states
        originals = {}
        for provider in Provider:
            account = states[provider].account
            windows = () if provider == Provider.DEEPSEEK else (
                QuotaWindow("five", "test", 300, 99.9, RecoveryKind.FIXED_RESET, now + timedelta(hours=23, minutes=59, seconds=59)),
                QuotaWindow("week", "test", 10080, 99.9, RecoveryKind.FIXED_RESET, now + timedelta(days=6, hours=23, minutes=59)))
            balances = (Balance("CNY", Decimal("99999.99"), is_available=True),) if provider == Provider.DEEPSEEK else ()
            originals[provider] = UsageSnapshot(account.id, provider, "synthetic-boundary", windows, balances, now)
        for scenario in ("normal", "loading", "disconnected", "error", "auth", "stale", "rate", "incompatible", "multi", "long"):
            for provider, state in states.items():
                state.snapshot = originals[provider]
                state.status = Status.FRESH
                state.error = None
                if scenario in ("loading", "disconnected", "error", "auth", "rate", "incompatible"):
                    state.snapshot = None
                    state.status = {"loading": Status.LOADING, "disconnected": Status.DISCONNECTED, "error": Status.OFFLINE,
                                    "auth": Status.AUTH_REQUIRED, "rate": Status.RATE_LIMITED, "incompatible": Status.INCOMPATIBLE}[scenario]
                    state.error = {"error": ErrorCode.NETWORK, "auth": ErrorCode.AUTH_REQUIRED,
                                   "rate": ErrorCode.RATE_LIMITED, "incompatible": ErrorCode.INCOMPATIBLE}.get(scenario)
                if scenario == "stale":
                    state.status, state.error = Status.STALE, ErrorCode.NETWORK
            if scenario == "multi":
                state = states[Provider.DEEPSEEK]
                state.snapshot = UsageSnapshot(state.account.id, state.account.provider, "synthetic-multicurrency", (),
                    (Balance("USD", Decimal("0.000000001"), is_available=True), Balance("CNY", Decimal("1.234567890123456789"), is_available=True)), now)
            if scenario == "long":
                state = states[Provider.DEEPSEEK]
                state.snapshot = UsageSnapshot(state.account.id, state.account.provider, "synthetic-long", (),
                                               (Balance("CNY", Decimal("1E+100"), is_available=True),), now)
            widget = LiveLeaf(runtime, expanded=True, reduced_motion=True)
            widget._pulse.stop()
            widget._now = lambda: now.astimezone()
            widget.audit_layout = True
            for edge in ("right", "left", "top", "bottom"):
                widget.set_dock_edge(edge)
                for detail in ("", "codex", "glm", "deepseek"):
                    widget.set_detail(detail)
                    widget.set_detail_opacity(1)
                    widget.layout_issues.clear()
                    image = widget.grab()
                    report["cases"] += 1
                    if widget.layout_issues:
                        report["issues"].append({"scenario": scenario, "edge": edge, "detail": detail, "text": widget.layout_issues.copy()})
                    if edge == "right":
                        image.save(str(args.out_dir / f"{scenario}-{detail or 'overview'}.png"))
            widget.close()
        (args.out_dir / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True))
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
