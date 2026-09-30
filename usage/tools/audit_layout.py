"""Render every M1 text state and check glyph bounds against the leaf contour."""

from __future__ import annotations

from _paths import EVIDENCE

import argparse
import json
import os
from datetime import timedelta
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--scale", type=float, default=1.0)
parser.add_argument("--edge", choices=("right", "left", "top", "bottom"), default="right")
parser.add_argument("--expected-dpr", type=float, help="Fail if the actual Qt pixel ratio differs from the intended review scale")
parser.add_argument("--out-dir", type=Path, default=Path(EVIDENCE / "m1-rework"))
args = parser.parse_args()
os.environ["QT_SCALE_FACTOR"] = str(args.scale)

from PySide6.QtWidgets import QApplication  # noqa: E402

from main import LeafPrototype, STATE_NAMES  # noqa: E402
from quota_visual import SCENARIOS  # noqa: E402


app = QApplication([])
widget = LeafPrototype(expanded=True)
widget.set_dock_edge(args.edge)
widget.move(100, 100)
widget.show()
widget._pulse.stop()
widget._tick.stop()
widget.audit_layout = True
app.processEvents()
actual_dpr = widget.devicePixelRatioF()
if args.expected_dpr is not None:
    assert abs(actual_dpr - args.expected_dpr) < .01, (actual_dpr, args.expected_dpr)

cases: list[tuple[str, str, str]] = []
for scenario in SCENARIOS:
    for detail in ("", "codex", "glm", "deepseek"):
        cases.append((scenario, "normal", detail))
for state in STATE_NAMES:
    for detail in ("", "codex", "glm", "deepseek"):
        cases.append(("baseline", state, detail))

failures = []
for scenario, state, detail in cases:
    widget.scenario = scenario
    widget.state = state
    widget.detail = detail
    widget._previous_detail = ""
    widget._detail_opacity = 1
    widget.update()
    app.processEvents()
    widget.grab()
    if widget.layout_issues:
        failures.append({"scenario": scenario, "state": state, "detail": detail, "issues": list(widget.layout_issues)})

long_cases = ("", "codex", "glm")
now = widget._now()
widget._five_at = now + timedelta(hours=10, minutes=59, seconds=59)
widget._week_at = now + timedelta(days=9, hours=23, minutes=59)
widget._glm_five_at = now + timedelta(hours=10, minutes=59, seconds=59)
widget.scenario = "baseline"
widget.state = "normal"
for detail in long_cases:
    widget.detail = detail
    widget.update()
    app.processEvents()
    widget.grab()
    if widget.layout_issues:
        failures.append({"scenario": "longest", "state": "normal", "detail": detail, "issues": list(widget.layout_issues)})

widget.copy_feedback = "已复制 · 需求澄清"
widget.detail = "codex"
widget.update()
app.processEvents()
widget.grab()
if widget.layout_issues:
    failures.append({"scenario": "copy-feedback", "state": "normal", "detail": "codex", "issues": list(widget.layout_issues)})

widget.copy_feedback = ""
widget.scenario = "baseline"
for state in STATE_NAMES:
    widget.state = state
    for focus in range(8):
        widget.keyboard_ball = focus
        widget.detail = ("codex", "glm", "deepseek")[focus] if focus < 3 else ""
        widget.unread_reminder = focus == 6
        widget._previous_detail = ""
        widget._detail_opacity = 1
        widget.update()
        app.processEvents()
        widget.grab()
        if widget.layout_issues:
            failures.append({"scenario": "keyboard-focus", "state": state, "detail": focus, "issues": list(widget.layout_issues)})

total_cases = len(cases) + len(long_cases) + 1 + len(STATE_NAMES) * 8
report = {"scale_factor": args.scale, "edge": args.edge, "device_pixel_ratio": actual_dpr,
          "cases": total_cases, "failures": failures}
out = args.out_dir
out.mkdir(parents=True, exist_ok=True)
(out / f"layout-{args.edge}-{args.scale:g}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"scale": args.scale, "dpr": actual_dpr, "edge": args.edge, "cases": total_cases, "failures": len(failures),
                  "first": failures[:3]}, ensure_ascii=True))
widget.close()
raise SystemExit(1 if failures else 0)
