"""Focused M1 checks against the running Qt widget and fixed presentation data."""

from __future__ import annotations

from _paths import EVIDENCE

import json
import platform
import sys
import ctypes
from ctypes.wintypes import POINT, RECT
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QFontMetricsF
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from countdown import present_countdown
from clipboard_win import clipboard_matches
from main import BALL_XS, BALL_YS, DETAIL_COUNTDOWN_X, DETAIL_META_X, DOCK_BENEFIT_X, DOCK_EXPOSURE, DOCK_RADIUS, DOCK_X, SAMPLE_TEXT, LeafPrototype, leaf_path
from quota_visual import LOW_REMAINING, SCENARIOS, QuotaSample, lowest_remaining, sample_for, tightest_provider_window


def check_countdowns() -> int:
    now = datetime(2026, 9, 27, 2, 10, tzinfo=ZoneInfo("Asia/Shanghai"))
    expected = {
        90061: "1天01时01分",
        86401: "1天00时00分",
        86400: "1天00时00分",
        86399: "23时59分59秒",
        36000: "10时00分00秒",
        35999: "9时59分59秒",
        3600: "1时00分00秒",
        3599: "0时59分59秒",
        60: "0时01分00秒",
        59: "0时00分59秒",
        1: "0时00分01秒",
        0: "0时00分00秒",
    }
    for seconds, text in expected.items():
        result = present_countdown(now + timedelta(seconds=seconds), now)
        assert result and result.text == text, (seconds, result)
        if seconds == 0:
            assert result.status == "awaiting_confirmation"
    assert present_countdown(None, now) is None
    return len(expected) + 1


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    checks = check_countdowns()
    for sample in SCENARIOS.values():
        for provider in ("codex", "glm"):
            for window in ("5h", "week"):
                value = sample.percent(provider, window)
                assert value is None or 0 <= value <= 100
                checks += 1
    assert sample_for("low", "normal").codex_5h <= LOW_REMAINING
    assert sample_for("low", "normal").glm_5h > LOW_REMAINING
    assert sample_for("unknown", "normal").codex_5h is None
    assert sample_for("baseline", "disconnected").deepseek_balance is None
    checks += 4
    assert lowest_remaining(SCENARIOS["low"]) == ("codex", "5h", 8)
    assert lowest_remaining(SCENARIOS["middle"]) == ("glm", "5h", 48)
    assert lowest_remaining(SCENARIOS["unknown"]) is None
    assert lowest_remaining(SCENARIOS["unknown"], include_week=True) == ("codex", "week", 42)
    assert lowest_remaining(QuotaSample(8, 60, 8, 60, "¥2")) == ("codex", "5h", 8)
    assert lowest_remaining(QuotaSample(0, None, None, None, None)) == ("codex", "5h", 0)
    checks += 6
    assert lowest_remaining(SCENARIOS["baseline"], include_week=True) == ("codex", "week", 42)
    assert lowest_remaining(SCENARIOS["abundant"], include_week=True) == ("glm", "week", 76)
    assert lowest_remaining(SCENARIOS["middle"], include_week=True) == ("codex", "week", 47)
    checks += 3
    assert tightest_provider_window(SCENARIOS["low"], "codex") == ("5h", 8)
    assert tightest_provider_window(SCENARIOS["low"], "glm") == ("week", 58)
    assert tightest_provider_window(SCENARIOS["unknown"], "codex") == ("week", 42)
    assert tightest_provider_window(SCENARIOS["all_unknown"], "glm") is None
    assert tightest_provider_window(QuotaSample(15, 15, None, None, None), "codex") == ("5h", 15)
    checks += 5
    widget = LeafPrototype(expanded=True)
    widget.move(100, 100)
    widget.show()
    app.processEvents()
    mask = widget.mask()
    assert mask.contains(QPoint(BALL_XS[0], BALL_YS[0]))
    assert mask.contains(QPoint(150, 130))
    assert not mask.contains(QPoint(5, 5))
    assert not mask.contains(QPoint(44, 64))  # transparent gap between spheres
    checks += 4
    widget.pinned = True
    widget.keyboard_ball = 0
    QTest.mouseClick(widget, Qt.MouseButton.LeftButton, pos=QPoint(133, 165))
    assert widget.detail == "codex" and not widget.pinned and widget.keyboard_ball == -1 and not widget.hasFocus()
    QTest.mouseClick(widget, Qt.MouseButton.LeftButton, pos=QPoint(180, 120))
    assert not widget.pinned and not widget.hasFocus()
    widget.collapse()
    QTest.qWait(210)
    assert widget._progress < .01
    widget.set_expansion_progress(1)
    checks += 3
    signatures = []
    for scenario in ("abundant", "middle", "low", "unknown", "all_unknown"):
        widget.scenario = scenario
        widget.set_expansion_progress(0)
        widget.update()
        app.processEvents()
        signatures.append(bytes(widget.grab().toImage().bits()))
    assert len(set(signatures)) == 5  # The exposed half-ball changes with the sample.
    trust_signatures = []
    for scenario, state in (("baseline", "normal"), ("baseline", "stale"),
                            ("partial_unknown", "normal"), ("baseline", "disconnected")):
        widget.scenario = scenario
        widget.state = state
        widget.update()
        app.processEvents()
        trust_signatures.append(bytes(widget.grab().toImage().bits()))
    assert len(set(trust_signatures)) == 4  # Equal visible readings must not conceal provenance changes.
    assert widget._trust_mark("glm", SCENARIOS["baseline"]) == ""
    widget.state = "stale"
    assert widget._trust_mark("glm", SCENARIOS["baseline"]) == "旧"
    widget.state = "normal"
    assert widget._trust_mark("codex", SCENARIOS["partial_unknown"]) == "缺"
    checks += 4
    assert DOCK_EXPOSURE == 44 and DOCK_RADIUS == 36 and DOCK_X == 292
    assert widget.mask().contains(QPoint(257, 130))
    assert not widget.mask().contains(QPoint(251, 130))
    assert widget._visible_hit(257, 130)
    assert not widget._visible_hit(255, 130)
    checks += 5
    widget.set_expansion_progress(1)
    assert widget._visible_hit(DOCK_X, 130)  # stationary dock hover does not oscillate
    assert not widget.mask().contains(QPoint(DOCK_X, 130))  # desktop click passes through
    checks += 2
    dock_global = widget.mapToGlobal(QPoint(DOCK_X, 130))
    widget.cursor = lambda: type("StationaryCursor", (), {"pos": lambda self: dock_global})()
    widget._last_inside = True
    widget._close_timer.stop()
    widget._check_cursor_and_animate()
    assert not widget._close_timer.isActive()
    del widget.cursor
    widget._last_inside = False
    checks += 1
    dock_half = QFontMetricsF(widget._font(7.0, bold=True)).boundingRect("半").translated(DOCK_BENEFIT_X, 146)
    assert dock_half.right() < widget.width() and dock_half.left() > 285
    dock_window_font = QFontMetricsF(widget._font(6.5, bold=True, numeric=True))
    assert max(dock_window_font.boundingRect(label).width() for label in ("H", "W", "?")) < 12
    checks += 2
    before_reminder = bytes(widget.grab().toImage().bits())
    widget.trigger_reminder_demo()
    app.processEvents()
    after_reminder = bytes(widget.grab().toImage().bits())
    assert before_reminder != after_reminder and widget.unread_reminder
    widget.acknowledge_reminder_demo()
    assert not widget.unread_reminder
    checks += 3
    widget.scenario = "baseline"
    widget.set_expansion_progress(1)
    checks += 1
    if platform.system() == "Windows":
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.WindowFromPoint.argtypes = [POINT]
        user32.WindowFromPoint.restype = ctypes.c_void_p
        owner = int(widget.winId())
        rect = RECT()
        assert user32.GetWindowRect(ctypes.c_void_p(owner), ctypes.byref(rect))
        ratio = widget.devicePixelRatioF()
        for x, y, expected in ((150, 130, True), (BALL_XS[0], BALL_YS[0], True), (44, 64, False), (5, 5, False)):
            hit = user32.WindowFromPoint(POINT(rect.left + round(x * ratio), rect.top + round(y * ratio)))
            assert (hit == owner) == expected, (x, y, hit, owner)
            checks += 1
        widget.set_expansion_progress(0)
        app.processEvents()
        for x, y, expected in ((257, 130, True), (290, 101, True), (290, 159, True), (251, 130, False)):
            hit = user32.WindowFromPoint(POINT(rect.left + round(x * ratio), rect.top + round(y * ratio)))
            assert (hit == owner) == expected, (x, y, hit, owner)
            checks += 1
        widget.set_expansion_progress(1)
    update_width = QFontMetricsF(widget._font(9)).horizontalAdvance("更新 02:09")
    assert leaf_path().contains(QPointF(DETAIL_META_X + update_width + 2, 42))
    assert DETAIL_META_X > 95 + QFontMetricsF(widget._font(9.5, bold=True)).horizontalAdvance("Codex") + 5
    seconds_width = QFontMetricsF(widget._font(9.3)).horizontalAdvance("秒")
    assert leaf_path().contains(QPointF(DETAIL_COUNTDOWN_X + 2 * 32 + 18 + seconds_width + 2, 68))
    assert DETAIL_COUNTDOWN_X > 95 + QFontMetricsF(widget._font(9)).horizontalAdvance("5h 03:40") + 3
    checks += 4
    assert widget._provider_at(133, 143) == "codex"
    assert widget._provider_at(133, 165) == "codex"
    assert widget._provider_at(133, 188) == "codex"
    assert widget._provider_at(220, 165) == "glm"
    assert widget._provider_at(180, 216) == "deepseek"
    checks += 5
    widget.set_detail("codex")
    widget.pinned = False
    QTest.mouseClick(widget, Qt.MouseButton.LeftButton, pos=QPoint(BALL_XS[0], BALL_YS[0]))
    assert QApplication.clipboard().text() == SAMPLE_TEXT
    assert clipboard_matches(SAMPLE_TEXT)
    assert widget.copy_feedback.startswith("已复制")
    checks += 3
    QTest.qWait(1850)
    assert widget.copy_feedback == ""  # Hover detail may clear after the pointer leaves.
    checks += 1
    widget.keyboard_ball = -1
    QTest.keyClick(widget, Qt.Key.Key_Tab)
    assert widget.keyboard_ball == 0 and widget.detail == "codex"
    QTest.qWait(190)
    widget.grab().save(str(EVIDENCE / "focus-platform.png"))
    for _ in range(3):
        QTest.keyClick(widget, Qt.Key.Key_Tab)
    assert widget.keyboard_ball == 3
    QTest.qWait(190)
    widget.grab().save(str(EVIDENCE / "focus-action.png"))
    QApplication.clipboard().clear()
    widget.trigger_reminder_demo()
    QTest.keyClick(widget, Qt.Key.Key_Return)
    assert QApplication.clipboard().text() == SAMPLE_TEXT
    assert widget.unread_reminder and widget.copy_feedback.startswith("已复制")
    QTest.keyClick(widget, Qt.Key.Key_Escape)
    assert not widget.pinned
    checks += 5
    widget._set_presentation("normal", "low")
    assert widget._previous_sample is not None and widget._graphic_value("codex", "5h") > 8
    QTest.qWait(250)
    assert widget._previous_sample is None and widget._graphic_value("codex", "5h") == 8
    widget._set_presentation("normal", "baseline")
    QTest.qWait(250)
    checks += 2
    for state in ("loading", "empty", "error", "stale", "disconnected"):
        widget.state = state
        widget.update()
        app.processEvents()
        assert widget.grab().width() > 0
    checks += 5
    widget.state = "normal"
    widget.clearFocus()
    widget.pinned = False
    widget._pulse.stop()
    widget._open_timer.stop()
    widget._close_timer.stop()
    for _ in range(30):
        widget._animate_to(0.0)
        QTest.qWait(210)
        assert widget._progress < .01
        assert widget._ball_at(BALL_XS[0], BALL_YS[0]) == -1
        widget._animate_to(1.0)
        QTest.qWait(310)
        assert widget._progress > .99
        assert widget._ball_at(BALL_XS[0], BALL_YS[0]) == 0
    checks += 120
    widget._animate_to(0.0)
    QTest.qWait(75)
    assert 0 < widget._progress < 1
    widget._animate_to(1.0)
    QTest.qWait(290)
    assert widget._progress > .99
    checks += 2
    widget.reduced_motion = True
    widget.trigger_reminder_demo()
    assert widget.unread_reminder and widget._reminder_animation.state().value == 0
    widget.acknowledge_reminder_demo()
    checks += 1
    widget._animate_to(0.0)
    assert widget._progress < .01
    widget._animate_to(1.0)
    assert widget._progress > .99 and widget._ball_progress(4) > .99
    checks += 2
    dimensions = leaf_path().boundingRect()
    screen = app.primaryScreen()
    report = {
        "checks_passed": checks,
        "platform": platform.platform(),
        "qt_screen": screen.name(),
        "device_pixel_ratio": screen.devicePixelRatio(),
        "core_path_bounds_dip": [round(dimensions.x(), 1), round(dimensions.y(), 1), round(dimensions.width(), 1), round(dimensions.height(), 1)],
        "window_bounds_dip": [widget.width(), widget.height()],
        "mask_bounds_dip": [mask.boundingRect().x(), mask.boundingRect().y(), mask.boundingRect().width(), mask.boundingRect().height()],
        "paint_frame_metrics": widget.frame_metrics(),
        "scope": "programmatic Qt checks plus eight Windows WindowFromPoint hit-test samples (expanded and docked); physical mouse feel and mixed-monitor DPI require user UAT",
    }
    path = Path(EVIDENCE / "m1-check.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    widget.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
