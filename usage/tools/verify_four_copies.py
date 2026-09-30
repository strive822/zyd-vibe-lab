"""Native Qt renders and own-widget checks without a second visible desktop leaf."""
from __future__ import annotations

from _paths import EVIDENCE

import argparse
import json
import math
import os
import tempfile
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float)
    parser.add_argument("--native-dpr", type=float, default=1.5, help="Reference screen's measured Windows DPI ratio")
    args = parser.parse_args()
    if args.scale is not None:
        os.environ["QT_SCALE_FACTOR"] = str(args.scale / args.native_dpr)
    from PIL import Image
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QEventLoop, QTimer

    from usage_app.desktop import DesktopLeaf
    from usage_app.models import Provider, Status
    from usage_app.parsers import GLM_PERSONAL_MAPPING, parse_codex, parse_deepseek, parse_glm
    from usage_app.runtime import UsageRuntime
    from usage_app.text_ui import SnippetSettings

    app = QApplication([])
    if args.scale is not None:
        assert abs(app.primaryScreen().devicePixelRatio() - args.scale) < .01
    app.setQuitOnLastWindowClosed(False)
    out = Path(EVIDENCE / "m6/four-copies") / str(round(app.primaryScreen().devicePixelRatio() * 100))
    out.mkdir(parents=True, exist_ok=True)
    checks = []
    with tempfile.TemporaryDirectory(prefix="duizhaoye-four-copies-") as directory:
        runtime = UsageRuntime(Path(directory))
        runtime.stop()
        now = datetime.now(UTC)
        for provider, state in runtime.states.items():
            state.account = replace(state.account, enabled=True)
            if provider == Provider.CODEX:
                state.snapshot = parse_codex({"rateLimits": {"primary": {"usedPercent": 28, "windowDurationMins": 300},
                                                            "secondary": {"usedPercent": 47, "windowDurationMins": 10080}}}, state.account, now)
            elif provider == Provider.GLM:
                state.snapshot = parse_glm({"data": {"limits": [{"type": "CREDIT_LIMIT", "unit": 3, "number": 5, "percentage": 0},
                                                                {"type": "CREDIT_LIMIT", "unit": 6, "number": 1, "percentage": 0,
                                                                 "nextResetTime": 1791350754998}]}}, state.account, now, GLM_PERSONAL_MAPPING)
            else:
                state.snapshot = parse_deepseek({"is_available": True, "balance_infos": [{"currency": "CNY", "total_balance": "42.11"}]}, state.account, now)
            state.status = Status.FRESH
        leaf = DesktopLeaf(runtime, reduced_motion=True)
        leaf.tray.hide()
        leaf._pulse.stop()
        leaf._tick.stop()
        leaf.ensurePolished()
        for index in range(4):
            item = leaf.snippets.store.add(f"常用文本 {index + 1}", icon_id=("copy", "text", "code", "check")[index], favorite_slot=index)
            leaf.snippets.store.path_for(item).write_bytes(f"独立正文 {index + 1}\n第二行".encode("utf-8"))
        extra = leaf.snippets.store.add("列表中的第五条")
        leaf.snippets.store.path_for(extra).write_text("更多文本正文", encoding="utf-8")
        leaf.snippets.reload()
        assert leaf._action_count() == 7 and leaf._reminder_ball_index() == 5
        for edge in ("right", "left", "top", "bottom"):
            leaf.set_dock_edge(edge)
            leaf.set_expansion_progress(1)
            centres = [leaf._ball_center(index) for index in range(7)]
            for index, centre in enumerate(centres):
                assert 20 <= centre.x() <= leaf.width() - 20 and 20 <= centre.y() <= leaf.height() - 20
                assert leaf._ball_at(centre.x(), centre.y()) == index
                assert leaf.mask().contains(centre.toPoint())
                assert leaf.mask().contains((centre + QPointF(0, 17)).toPoint())
            assert min(math.hypot(a.x() - b.x(), a.y() - b.y()) for index, a in enumerate(centres) for b in centres[index + 1:]) >= 36
            assert leaf.grab().save(str(out / f"{edge}.png"))
            leaf.reduced_motion = False
            for frame in range(29):
                leaf.set_expansion_progress(frame / 28)
                for index in range(7):
                    if leaf._ball_progress(index) > .04:
                        centre = leaf._ball_center(index)
                        assert 20 <= centre.x() <= leaf.width() - 20 and 20 <= centre.y() <= leaf.height() - 20
            leaf.reduced_motion = True
        checks.append("four orientations: seven non-overlapping 36 DIP targets, full mask and all animation positions within bounds")
        leaf.set_dock_edge("right")
        leaf.set_expansion_progress(1)
        # A capture sink verifies routing/text without replacing the user's
        # clipboard. The native Unicode transport is checked separately in M4.
        written = []
        leaf.snippets.clipboard.write = lambda owner, text: written.append(text)
        for index in range(4):
            leaf._activate_ball(index)
            assert written[-1] == f"独立正文 {index + 1}\n第二行"
            assert leaf._copy_confirmed(index)
            assert not leaf._copy_confirmed((index + 1) % 4)
        leaf.snippets.copy(extra.id, int(leaf.winId()))
        assert written[-1] == "更多文本正文"
        checks.append("four stable favorite IDs copy four independent saved bodies; additional named text remains accessible")

        def icon():
            image = QImage(32, 32, QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            painter.translate(16, 16)
            leaf._paint_icon(painter, 5, QColor("#1e2119"))
            painter.end()
            return image
        leaf._clear_feedback()
        before = icon()
        leaf._activate_ball(3)
        assert icon() == before
        checks.append("fourth-copy feedback does not turn the reminder icon into a checkmark")
        leaf._clear_feedback()
        leaf._reset_keyboard_focus()
        visited = []
        for index in range(10):
            leaf._focus_next(1)
            visited.append(leaf.keyboard_ball)
            if index >= 3:
                assert leaf._focused_action_index() == index - 3
        assert visited == list(range(10))
        leaf._focus_next(1)
        assert leaf.keyboard_ball == 0
        routed = []
        leaf.open_more_texts = lambda: routed.append("more")
        leaf.open_reminders = lambda: routed.append("reminders")
        leaf.open_text_settings = lambda: routed.append("settings")
        for index in (4, 5, 6):
            leaf._activate_ball(index)
        assert routed == ["more", "reminders", "settings"]
        checks.append("Tab traverses three providers and seven actions; more/reminders/settings route to correct destinations")
        leaf._reset_keyboard_focus()
        leaf.unread_reminder = True
        leaf.grab().save(str(out / "reminder.png"))
        panel = SnippetSettings(leaf.snippets)
        assert [panel.favorite.itemData(index) for index in range(panel.favorite.count())] == [None, 0, 1, 2, 3]
        panel.grab().save(str(out / "settings-four-slots.png"))
        checks.append("settings exposes all four common slots; existing first and second slots retain identities")
        panel.close()
        def pump(milliseconds):
            loop = QEventLoop()
            QTimer.singleShot(milliseconds, loop.quit)
            loop.exec()
        leaf.set_dock_edge("right")
        leaf.pinned = False
        leaf.hasFocus = lambda: False
        leaf._visible_hit = lambda x, y: False
        leaf._last_inside = True
        leaf.set_expansion_progress(1)
        leaf._pulse.start(32)
        pump(1100)
        assert leaf._progress == 0 and leaf._pulse.isActive() and leaf._pulse.interval() == 64
        leaf._visible_hit = lambda x, y: True
        pump(500)  # Deliberately no Qt Enter event.
        assert leaf._progress == 1 and leaf._pulse.isActive() and leaf._pulse.interval() == 32
        pump(200)
        assert leaf._progress == 1
        leaf._visible_hit = lambda x, y: False
        pump(1100)
        assert leaf._progress == 0 and leaf._pulse.isActive()
        checks.append("continuous 64ms collapsed polling wakes without Enter, stays expanded on hover, and returns to quiet polling after leave")
        leaf.quit_app()
    frames = []
    for edge in ("right", "left", "top", "bottom"):
        with Image.open(out / f"{edge}.png") as frame:
            frames.append(frame.convert("RGBA"))
    strip = Image.new("RGBA", (sum(frame.width for frame in frames), max(frame.height for frame in frames)), "#e5e4da")
    x = 0
    for frame in frames:
        strip.alpha_composite(frame, (x, 0))
        x += frame.width
    strip.convert("RGB").save(out / "four-edges.png")
    report = {"passed": len(checks), "checks": checks, "nativeDpr": app.primaryScreen().devicePixelRatio(),
              "boundary": "Windows native Qt painting and own-widget operations without showing a second leaf or altering the user clipboard. Synthetic account values. Scale override is render simulation, not mixed-DPI physical validation."}
    (out / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
