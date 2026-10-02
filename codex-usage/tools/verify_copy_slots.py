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
    from usage_app.clipboard import ClipboardError
    from usage_app.models import Provider, Status
    from usage_app.parsers import GLM_PERSONAL_MAPPING, parse_codex, parse_deepseek, parse_glm
    from usage_app.runtime import UsageRuntime
    from usage_app.text_ui import SnippetSettings

    app = QApplication([])
    if args.scale is not None:
        assert abs(app.primaryScreen().devicePixelRatio() - args.scale) < .01
    app.setQuitOnLastWindowClosed(False)
    out = Path(EVIDENCE / "m6/six-copies") / str(round(app.primaryScreen().devicePixelRatio() * 100))
    out.mkdir(parents=True, exist_ok=True)
    checks = []
    with tempfile.TemporaryDirectory(prefix="usage-six-copies-") as directory:
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
        for index in range(6):
            item = leaf.snippets.store.add(f"常用文本 {index + 1}", icon_id=("copy", "text", "code", "check", "note", "copy")[index], favorite_slot=index)
            leaf.snippets.store.path_for(item).write_bytes(f"独立正文 {index + 1}\n第二行".encode("utf-8"))
        extra = leaf.snippets.store.add("列表中的第七条")
        leaf.snippets.store.path_for(extra).write_text("更多文本正文", encoding="utf-8")
        leaf.snippets.reload()
        assert leaf._action_count() == 9 and leaf._reminder_ball_index() == 7
        for edge in ("right", "left", "top", "bottom"):
            leaf.set_dock_edge(edge)
            leaf.set_expansion_progress(1)
            centres = [leaf._ball_center(index) for index in range(9)]
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
                for index in range(9):
                    if leaf._ball_progress(index) > .04:
                        centre = leaf._ball_center(index)
                        assert 20 <= centre.x() <= leaf.width() - 20 and 20 <= centre.y() <= leaf.height() - 20
            leaf.reduced_motion = True
        checks.append("four orientations: nine non-overlapping 36 DIP targets, full mask and all animation positions within bounds")
        leaf.set_dock_edge("right")
        leaf.set_expansion_progress(1)
        # A capture sink verifies routing/text without replacing the user's
        # clipboard. The native Unicode transport is checked separately in M4.
        written = []
        leaf.snippets.clipboard.write = lambda owner, text: written.append(text)
        for index in range(6):
            leaf._activate_ball(index)
            assert written[-1] == f"独立正文 {index + 1}\n第二行"
            assert leaf._copy_confirmed(index)
            assert not leaf._copy_confirmed((index + 1) % 6)
        leaf.snippets.copy(extra.id, int(leaf.winId()))
        assert written[-1] == "更多文本正文"
        checks.append("six stable favorite IDs copy six independent saved bodies; additional named text remains accessible")

        def icon():
            image = QImage(32, 32, QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            painter.translate(16, 16)
            leaf._paint_icon(painter, 7, QColor("#1e2119"))
            painter.end()
            return image
        leaf._clear_feedback()
        before = icon()
        leaf._activate_ball(5)
        assert icon() == before
        checks.append("sixth-copy feedback does not turn the reminder icon into a checkmark")
        leaf._clear_feedback()
        leaf._reset_keyboard_focus()
        visited = []
        for index in range(12):
            leaf._focus_next(1)
            visited.append(leaf.keyboard_ball)
            if index >= 3:
                assert leaf._focused_action_index() == index - 3
        assert visited == list(range(12))
        leaf._focus_next(1)
        assert leaf.keyboard_ball == 0
        routed = []
        leaf.open_more_texts = lambda: routed.append("more")
        leaf.open_reminders = lambda: routed.append("reminders")
        leaf.open_text_settings = lambda: routed.append("settings")
        for index in (6, 7, 8):
            leaf._activate_ball(index)
        assert routed == ["more", "reminders", "settings"]
        checks.append("Tab traverses three providers and nine actions; more/reminders/settings route to correct destinations")
        leaf._reset_keyboard_focus()
        leaf.unread_reminder = True
        leaf.grab().save(str(out / "reminder.png"))
        panel = SnippetSettings(leaf.snippets)
        assert [panel.favorite.itemData(index) for index in range(panel.favorite.count())] == [None, 0, 1, 2, 3, 4, 5]
        panel.grab().save(str(out / "settings-six-slots.png"))
        checks.append("settings exposes all six common slots with stable slot identifiers")
        panel.close()
        leaf._clear_feedback()
        leaf.keyboard_ball = 8  # Three providers followed by the sixth copy.
        leaf.grab().save(str(out / "sixth-focus.png"))
        leaf._reset_keyboard_focus()
        written_before_failure = len(written)
        def denied(owner, text):
            raise ClipboardError("剪贴板暂时不可用，请重试")
        leaf.snippets.clipboard.write = denied
        leaf._activate_ball(5)
        assert leaf._copy_result and not leaf._copy_result.succeeded
        assert leaf.copy_feedback == "复制失败" and icon() == before
        leaf.grab().save(str(out / "sixth-error.png"))
        leaf._clear_feedback()
        sixth = leaf.snippets.favorite(5)
        assert sixth is not None
        leaf.snippets.store.update(sixth.id, name=sixth.name, description=sixth.description,
                                   icon_id=sixth.icon_id, favorite_slot=None)
        leaf.snippets.reload()
        leaf._activate_ball(5)
        assert leaf._copy_result and not leaf._copy_result.succeeded
        assert "设置" in leaf._copy_result.message and len(written) == written_before_failure
        leaf.grab().save(str(out / "sixth-unconfigured.png"))
        leaf._clear_feedback()
        checks.append("sixth-slot focus, clipboard failure and unconfigured states render without false success or reminder changes")
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
