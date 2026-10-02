"""对照叶 M1: one real Windows widget with fixed demonstration data.

The five action spheres are visual prototypes. Only the first copy action is live.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PySide6.QtCore import QEasingCurve, QPoint, QPointF, QRectF, QPropertyAnimation, QTimer, Qt, Property
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QGuiApplication, QPainter, QPainterPath, QPen, QRegion, QTransform
from PySide6.QtWidgets import QApplication, QToolTip, QWidget

from countdown import Countdown, present_countdown
from palette_visual import Palette, candidate
from quota_visual import LOW_REMAINING, SCENARIOS, QuotaSample, lowest_remaining, sample_for, tightest_provider_window


WIDTH, HEIGHT = 300, 260
VERTICAL_HEIGHT = 300
DOCK_EXPOSURE = 44
DOCK_RADIUS = 36
DOCK_X = WIDTH - DOCK_EXPOSURE + DOCK_RADIUS
DOCK_Y = 130
DOCK_LEFT = WIDTH - DOCK_EXPOSURE
DOCK_RING_X = DOCK_LEFT + 12
DOCK_BENEFIT_X = DOCK_LEFT + 31
DOCK_CENTERS = {
    "right": QPointF(DOCK_X, DOCK_Y),
    "left": QPointF(8, DOCK_Y),
    "top": QPointF(WIDTH / 2, 30),
    "bottom": QPointF(WIDTH / 2, HEIGHT - 30),
}
DETAIL_META_X = 143  # The leaf is narrow at the top; keep the update stamp inside its contour.
DETAIL_COUNTDOWN_X = 149
INK = QColor("#1e2119")
OLIVE = QColor("#58623d")
PAPER = QColor("#f5f2e9")
MUTED = QColor("#686c63")
RULE = QColor("#c9c9b9")
CONTOUR = QColor("#9fa48f")
CONTOUR_WIDTH = 1.2
WARM = QColor("#9d563c")
BALL_YS = (42, 86, 130, 174, 218)
BALL_XS = (61, 46, 47, 45, 63)  # 15 DIP of air from the leaf's left contour at each height.
VERTICAL_BALL_XS = (45, 96, 150, 204, 255)
TOP_BALL_YS = (257, 269, 274, 269, 257)
BOTTOM_BALL_YS = (43, 31, 26, 31, 43)
BALL_NAMES = ("复制 · 需求澄清", "复制 · 代码评审", "更多文本", "每日提醒", "设置")
FOCUS_PROVIDERS = ("codex", "glm", "deepseek")
SAMPLE_TEXT = "请先说明目标、约束和验收方式，再开始实现。"
STATE_NAMES = ("normal", "loading", "empty", "error", "stale", "disconnected")


def qcolor(color: QColor, alpha: float) -> QColor:
    result = QColor(color)
    result.setAlphaF(max(0.0, min(1.0, alpha)))
    return result


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) ** 3


def leaf_path() -> QPainterPath:
    path = QPainterPath(QPointF(78, 130))
    path.cubicTo(72, 83, 77, 42, 109, 29)
    path.cubicTo(159, 10, 253, 47, 285, 119)
    path.cubicTo(290, 129, 289, 138, 281, 148)
    path.cubicTo(265, 187, 266, 217, 247, 225)
    path.cubicTo(211, 240, 145, 239, 109, 227)
    path.cubicTo(76, 215, 70, 173, 78, 130)
    path.closeSubpath()
    return path


class LeafPrototype(QWidget):
    def __init__(self, state: str = "normal", expanded: bool = False, detail: str = "", reduced_motion: bool = False, scenario: str = "baseline", palette: Palette | None = None):
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("对照叶 · Visual Prototype")
        self.setAccessibleName("对照叶用量浮窗")
        self._default_accessible_description = "收起半球上方 C 表盘表示 Codex、下方 G 表盘表示 GLM；每枚表盘取该平台五小时与周窗口中最低的已知剩余，表盘内 H 表示五小时、W 表示周。完整底环提供比例参照，断续环与问号表示两个窗口都未知。底部人民币符号表示 DeepSeek 余额状态；顶部铃形表示未读提醒。Tab 可访问平台与动作。"
        self.setAccessibleDescription(self._default_accessible_description)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedSize(WIDTH, HEIGHT)
        self._leaf = leaf_path()
        self._shell_leaf_points = [self._leaf.pointAtPercent(index / 72) for index in range(72)]
        self.state = state
        self.palette = palette if palette is not None else candidate("H3")
        self.scenario = scenario
        self.detail = detail
        self.dock_edge: str | None = "right"
        self._free_edge = "right"
        self._drag_pending = False
        self._drag_started = False
        self._drag_press_ball = -1
        self._drag_origin_global = QPoint()
        self._drag_origin_window = QPoint()
        self.pinned = False
        self.hover_ball = -1
        self.keyboard_ball = -1
        self.reduced_motion = reduced_motion
        self.copy_feedback = ""
        self.unread_reminder = False
        self._reminder_pulse = 0.0
        self.audit_layout = False
        self.layout_issues: list[str] = []
        self._progress = 1.0 if expanded else 0.0
        self._detail_opacity = 1.0
        self._previous_detail = ""
        self._previous_sample: QuotaSample | None = None
        self._quota_blend = 1.0
        self._digit_transitions: dict[str, tuple[str, float]] = {}
        self._last_tick_text: dict[str, str] = {}
        self._countdown_previous: dict[str, Countdown] = {}
        self._countdown_motion: dict[str, tuple[Countdown, Countdown, float]] = {}
        self._frame_ms: list[float] = []
        self._last_inside = False
        self._clock_shift = 0
        self._started_at = time.monotonic()
        self._base_now = datetime(2026, 9, 27, 2, 10, tzinfo=ZoneInfo("Asia/Shanghai"))
        self._five_at = self._base_now + timedelta(hours=1, minutes=30)
        self._week_at = self._base_now + timedelta(days=3)
        self._glm_five_at = self._base_now + timedelta(hours=3, minutes=18)
        self._glm_week_at = None  # Do not invent a GLM recovery time.
        self._expansion = QPropertyAnimation(self, b"expansionProgress", self)
        self._expansion.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._detail_animation = QPropertyAnimation(self, b"detailOpacity", self)
        self._detail_animation.setDuration(170)
        self._detail_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._detail_animation.finished.connect(self._finish_detail_swap)
        self._quota_animation = QPropertyAnimation(self, b"quotaBlend", self)
        self._quota_animation.setDuration(220)
        self._quota_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._quota_animation.finished.connect(self._finish_quota_blend)
        self._reminder_animation = QPropertyAnimation(self, b"reminderPulse", self)
        self._reminder_animation.setDuration(650)
        self._reminder_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._open_timer = QTimer(self)
        self._open_timer.setSingleShot(True)
        self._open_timer.timeout.connect(self.expand)
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self.collapse)
        self._detail_timer = QTimer(self)
        self._detail_timer.setSingleShot(True)
        self._detail_timer.timeout.connect(self._clear_unpinned_detail)
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._commit_hover_detail)
        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)
        self._feedback_timer.timeout.connect(self._clear_feedback)
        self._tick = QTimer(self)
        self._tick.timeout.connect(self._on_tick)
        self._tick.start(1000)
        self._pulse = QTimer(self)
        self._pulse.timeout.connect(self._check_cursor_and_animate)
        self._pulse.start(32)
        self._update_mask()

    def _sample(self) -> QuotaSample:
        return sample_for(self.scenario, self.state)

    def _graphic_value(self, provider: str, window: str) -> float | None:
        current = self._sample().percent(provider, window)
        previous = self._previous_sample.percent(provider, window) if self._previous_sample else None
        if current is None or previous is None:
            return current
        return previous + (current - previous) * self._quota_blend

    def _provider_color(self, provider: str) -> QColor:
        return self.palette.codex if provider == "codex" else self.palette.glm

    def _quota_color(self, provider: str, percent: float) -> QColor:
        return self.palette.low if percent <= LOW_REMAINING else self._provider_color(provider)

    def _provider_stale(self, provider: str) -> bool:
        # The M1 stale fixture represents GLM's retained snapshot; the other
        # providers remain current. Keep that attribution explicit in both
        # the dock and the expanded detail.
        return self.state == "stale" and provider == "glm"

    def _provider_partial(self, provider: str, sample: QuotaSample) -> bool:
        return sum(sample.percent(provider, window) is None for window in ("5h", "week")) == 1

    def _trust_mark(self, provider: str, sample: QuotaSample) -> str:
        if self._provider_stale(provider):
            return "旧"
        if self._provider_partial(provider, sample):
            return "缺"
        return ""

    def _set_presentation(self, state: str, scenario: str | None = None) -> None:
        previous = self._sample()
        self.state = state
        if scenario is not None:
            self.scenario = scenario
        if self.reduced_motion:
            self._previous_sample = None
            self._quota_blend = 1.0
        else:
            self._quota_animation.stop()
            self._previous_sample = previous
            self._quota_blend = 0.0
            self._quota_animation.setStartValue(0.0)
            self._quota_animation.setEndValue(1.0)
            self._quota_animation.start()
        self.update()

    def _finish_quota_blend(self) -> None:
        self._previous_sample = None
        self.update()

    def get_quota_blend(self) -> float:
        return self._quota_blend

    def set_quota_blend(self, value: float) -> None:
        self._quota_blend = value
        self.update()

    quotaBlend = Property(float, get_quota_blend, set_quota_blend)

    def get_reminder_pulse(self) -> float:
        return self._reminder_pulse

    def set_reminder_pulse(self, value: float) -> None:
        self._reminder_pulse = value
        self.update()

    reminderPulse = Property(float, get_reminder_pulse, set_reminder_pulse)

    def trigger_reminder_demo(self) -> None:
        """Visual trigger only; scheduling and notifications belong to M5."""
        self.unread_reminder = True
        self._reminder_animation.stop()
        self._reminder_pulse = 0.0
        if not self.reduced_motion:
            self._reminder_animation.setStartValue(0.0)
            self._reminder_animation.setEndValue(1.0)
            self._reminder_animation.start()
        self.update()

    def acknowledge_reminder_demo(self) -> None:
        self.unread_reminder = False
        self._reminder_animation.stop()
        self._reminder_pulse = 0.0
        self.update()

    def get_expansion_progress(self) -> float:
        return self._progress

    def set_expansion_progress(self, value: float) -> None:
        self._progress = value
        self._update_mask()
        self.update()

    expansionProgress = Property(float, get_expansion_progress, set_expansion_progress)

    def get_detail_opacity(self) -> float:
        return self._detail_opacity

    def set_detail_opacity(self, value: float) -> None:
        self._detail_opacity = value
        self.update()

    detailOpacity = Property(float, get_detail_opacity, set_detail_opacity)

    def _now(self) -> datetime:
        return self._base_now + timedelta(seconds=time.monotonic() - self._started_at + self._clock_shift)

    def _on_tick(self) -> None:
        self.update()

    def _ball_progress(self, index: int) -> float:
        if self.reduced_motion:
            return self._progress
        elapsed = self._progress * 280
        if self._visual_edge() == "left":
            # The leaf grows across the left gutter. Let its contour clear
            # that gutter before the action spheres become visible.
            return ease((elapsed - (95 + 15 * index)) / 120)
        return ease((elapsed - (40 + 20 * index)) / 160)

    def _ball_center(self, index: int) -> QPointF:
        amount = self._ball_progress(index)
        edge = self._visual_edge()
        if edge == "left":
            return QPointF(WIDTH - BALL_XS[index] - 13 * (1 - amount), BALL_YS[index])
        if edge == "top":
            return QPointF(VERTICAL_BALL_XS[index], TOP_BALL_YS[index] - 13 * (1 - amount))
        if edge == "bottom":
            return QPointF(VERTICAL_BALL_XS[index], BOTTOM_BALL_YS[index] + 13 * (1 - amount))
        return QPointF(BALL_XS[index] + 13 * (1 - amount), BALL_YS[index])

    def set_dock_edge(self, edge: str | None) -> None:
        if edge not in (*DOCK_CENTERS, None):
            raise ValueError(edge)
        if edge is not None:
            self._free_edge = edge
        self.dock_edge = edge
        self.setFixedSize(WIDTH, VERTICAL_HEIGHT if self._visual_edge() in ("top", "bottom") else HEIGHT)
        self._update_mask()
        self.update()

    def _visual_edge(self) -> str:
        return self.dock_edge or self._free_edge

    def _content_offset(self) -> tuple[float, float]:
        if self._visual_edge() == "left":
            return -50, 0
        if self._visual_edge() == "top":
            return -30, 0
        if self._visual_edge() == "bottom":
            return -30, 50
        return 0, 0

    def _shell_target(self) -> QPainterPath:
        if self._visual_edge() == "left":
            return QTransform(-1, 0, 0, 1, WIDTH, 0).map(self._leaf)
        dx, dy = self._content_offset()
        return QTransform(1, 0, 0, 1, dx, dy).map(self._leaf)

    def _target_point(self, point: QPointF) -> QPointF:
        if self._visual_edge() == "left":
            return QPointF(WIDTH - point.x(), point.y())
        dx, dy = self._content_offset()
        return QPointF(point.x() + dx, point.y() + dy)

    def _dock_center(self) -> QPointF:
        if self._visual_edge() == "bottom":
            return QPointF(WIDTH / 2, self.height() - 30)
        return DOCK_CENTERS[self._visual_edge()]

    def _dock_dial_center(self, provider: str) -> QPointF:
        edge = self._visual_edge()
        if edge == "right":
            return QPointF(DOCK_RING_X + 8.5, 118.5 if provider == "codex" else 140.5)
        if edge == "left":
            return QPointF(23.5, 118.5 if provider == "codex" else 140.5)
        center = self._dock_center()
        return QPointF(center.x() - 2.5, center.y() + (-11.5 if provider == "codex" else 10.5))

    def _shell_path(self) -> QPainterPath:
        """One contour grows from the exposed circle into the same fixed leaf."""
        if self._progress <= .001:
            circle = QPainterPath()
            dock = self._dock_center()
            circle.addEllipse(QRectF(dock.x() - DOCK_RADIUS, dock.y() - DOCK_RADIUS,
                                     2 * DOCK_RADIUS, 2 * DOCK_RADIUS))
            return circle
        if self._progress >= .999:
            return self._shell_target()
        amount = ease(min(1.0, self._progress * 280 / 220))
        path = QPainterPath()
        dock = self._dock_center()
        for index, raw_leaf_point in enumerate(self._shell_leaf_points):
            leaf_point = self._target_point(raw_leaf_point)
            angle = math.pi + 2 * math.pi * index / len(self._shell_leaf_points)
            circle_x = dock.x() + DOCK_RADIUS * math.cos(angle)
            circle_y = dock.y() + DOCK_RADIUS * math.sin(angle)
            point = QPointF(circle_x + (leaf_point.x() - circle_x) * amount,
                            circle_y + (leaf_point.y() - circle_y) * amount)
            if index == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        path.closeSubpath()
        return path

    def _update_mask(self) -> None:
        # The native hit mask follows the same single visible shell; the 2 DIP
        # dilation leaves antialiased outline pixels intact without a large
        # transparent rectangle that would intercept the desktop.
        shell_region = QRegion(self._shell_path().toFillPolygon().toPolygon())
        region = shell_region
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            region = region.united(shell_region.translated(dx, dy))
        for index in range(5):
            if self._ball_progress(index) > 0.04:
                center = self._ball_center(index)
                region = region.united(QRegion(round(center.x() - 20), round(center.y() - 20), 40, 40, QRegion.RegionType.Ellipse))
        self.setMask(region)

    def _animate_to(self, target: float) -> None:
        self._expansion.stop()
        if self.reduced_motion:
            self.set_expansion_progress(target)
            return
        self._expansion.setStartValue(self._progress)
        self._expansion.setEndValue(target)
        duration = max(50, round((280 if target else 180) * abs(target - self._progress)))
        self._expansion.setDuration(duration)
        self._expansion.start()

    def expand(self) -> None:
        self._open_timer.stop()
        self._close_timer.stop()
        self._animate_to(1.0)

    def collapse(self) -> None:
        if self.dock_edge is None or self._drag_pending or self.pinned or self.hasFocus():
            return
        self._hover_timer.stop()
        self._detail_timer.stop()
        self._animate_to(0.0)

    def _check_cursor_and_animate(self) -> None:
        if self._drag_pending:
            return
        local = self.mapFromGlobal(self.cursor().pos())
        inside = self._visible_hit(local.x(), local.y())
        if inside and not self._last_inside:
            self._close_timer.stop()
            if self._progress < 0.05:
                self._open_timer.start(100)
            elif self._progress < 1:
                self.expand()
        if not inside and self._last_inside:
            self._open_timer.stop()
            self._hover_timer.stop()
            if self.dock_edge is not None and not self.pinned and not self.hasFocus():
                self._close_timer.start(700)
        self._last_inside = inside
        if not inside:
            self.unsetCursor()
            if self.hover_ball != -1:
                self.hover_ball = -1
                QToolTip.hideText()
                self.update()
            return
        if self._progress <= 0.9 and QWidget.cursor(self).shape() != Qt.CursorShape.OpenHandCursor:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        if self._progress > 0.9:
            new_ball = self._ball_at(local.x(), local.y())
            desired_cursor = Qt.CursorShape.PointingHandCursor if new_ball >= 0 else Qt.CursorShape.OpenHandCursor
            if QWidget.cursor(self).shape() != desired_cursor:
                self.setCursor(desired_cursor)
            if new_ball != self.hover_ball:
                self.hover_ball = new_ball
                if new_ball >= 0:
                    self._show_ball_tip(new_ball, BALL_NAMES[new_ball])
                else:
                    QToolTip.hideText()
                self.update()
            provider = self._provider_at(local.x(), local.y())
            if provider and provider != self.detail and not self.pinned:
                if getattr(self, "_hover_target", None) != provider or not self._hover_timer.isActive():
                    self._hover_target = provider
                    self._hover_timer.start(130)
                self._detail_timer.stop()
            elif provider is None:
                self._hover_timer.stop()
                if not self.pinned and self.detail and not self._detail_timer.isActive() and not self._inside_reading_area(local.x(), local.y()):
                    self._detail_timer.start(260)

    def _visible_hit(self, x: float, y: float) -> bool:
        # Keep the original dock position as a hover-only bridge after the
        # painted ball disappears. The native window mask still excludes that
        # empty area, so desktop clicks continue to pass through it.
        dock = self._dock_center()
        if self.dock_edge is not None and (x - dock.x()) ** 2 + (y - dock.y()) ** 2 <= DOCK_RADIUS ** 2:
            return True
        if self._shell_path().contains(QPointF(x, y)):
            return True
        return self._ball_at(x, y) >= 0

    def _ball_at(self, x: float, y: float) -> int:
        for index in range(5):
            if self._ball_progress(index) < 0.98:
                continue
            center = self._ball_center(index)
            if (x - center.x()) ** 2 + (y - center.y()) ** 2 <= 18 ** 2:
                return index
        return -1

    def _ball_tip_position(self, index: int, label: str) -> QPoint:
        """Keep action help outside the leaf's reading area."""
        center = self._ball_center(index)
        metrics = QFontMetricsF(QToolTip.font())
        width = math.ceil(metrics.horizontalAdvance(label)) + 24
        height = math.ceil(metrics.height()) + 16
        screen = self.screen().availableGeometry()
        edge = self._visual_edge()
        if edge == "left":
            local = QPoint(round(center.x() + 25), round(center.y() - height / 2))
        elif edge == "top":
            local = QPoint(round(center.x() - width / 2), round(center.y() + 24))
        elif edge == "bottom":
            local = QPoint(round(center.x() - width / 2), round(center.y() - 24 - height))
        else:
            local = QPoint(round(center.x() - 25 - width), round(center.y() - height / 2))
        global_top_left = self.mapToGlobal(local)
        return QPoint(min(max(global_top_left.x(), screen.left() + 4), screen.right() - width - 3),
                      min(max(global_top_left.y(), screen.top() + 4), screen.bottom() - height - 3))

    def _show_ball_tip(self, index: int, label: str) -> None:
        QToolTip.showText(self._ball_tip_position(index, label), label, self)

    def _provider_at(self, x: float, y: float) -> str | None:
        dx, dy = self._content_offset()
        x -= dx
        y -= dy
        if 133 <= y <= 197:
            if 124 <= x < 192:
                return "codex"
            if 192 <= x <= 263:
                return "glm"
        if 200 <= y <= 232 and 95 <= x <= 260:
            return "deepseek"
        return None

    def _inside_reading_area(self, x: float, y: float) -> bool:
        dx, dy = self._content_offset()
        x -= dx
        y -= dy
        return 75 <= x <= 271 and 42 <= y <= 199

    def _commit_hover_detail(self) -> None:
        self.set_detail(getattr(self, "_hover_target", ""))

    def _clear_unpinned_detail(self) -> None:
        if not self.pinned:
            self.set_detail("")

    def set_detail(self, detail: str) -> None:
        if detail == self.detail:
            return
        self._previous_detail = self.detail
        self.detail = detail
        self._detail_animation.stop()
        if self.reduced_motion:
            self._detail_opacity = 1.0
            self._previous_detail = ""
            self.update()
            return
        self._detail_opacity = 0.0
        self._detail_animation.setStartValue(0.0)
        self._detail_animation.setEndValue(1.0)
        self._detail_animation.start()
        self.update()

    def _finish_detail_swap(self) -> None:
        self._previous_detail = ""
        self.update()

    def _clear_feedback(self) -> None:
        self.copy_feedback = ""
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        self._drag_pending = True
        self._drag_started = False
        self._drag_origin_global = event.globalPosition().toPoint()
        self._drag_origin_window = self.pos()
        self._drag_press_ball = self._ball_at(event.position().x(), event.position().y()) if self._progress > .9 else -1
        self._open_timer.stop()
        self._close_timer.stop()
        self._hover_timer.stop()
        self._detail_timer.stop()
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pending and event.buttons() & Qt.MouseButton.LeftButton:
            if self._drag_press_ball >= 0:
                event.accept()
                return
            delta = event.globalPosition().toPoint() - self._drag_origin_global
            if not self._drag_started and delta.manhattanLength() >= QApplication.startDragDistance():
                self._drag_started = True
                self.pinned = False
                self._reset_keyboard_focus()
                self.hover_ball = -1
                self.clearFocus()
                QToolTip.hideText()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            if self._drag_started:
                self.move(self._drag_origin_window + delta)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or not self._drag_pending:
            super().mouseReleaseEvent(event)
            return
        was_dragging = self._drag_started
        self._drag_pending = False
        self._drag_started = False
        if was_dragging:
            self._finish_drag(event.globalPosition().toPoint())
        elif self._drag_press_ball < 0 or self._drag_press_ball == self._ball_at(event.position().x(), event.position().y()):
            self._perform_click(event.position().x(), event.position().y())
        self._drag_press_ball = -1
        local = self.mapFromGlobal(event.globalPosition().toPoint())
        self.setCursor(Qt.CursorShape.OpenHandCursor if self._visible_hit(local.x(), local.y()) else Qt.CursorShape.ArrowCursor)
        event.accept()

    def _finish_drag(self, pointer: QPoint) -> None:
        screen = QGuiApplication.screenAt(pointer) or self.screen() or QGuiApplication.primaryScreen()
        work = screen.availableGeometry()
        maximum_x = max(work.left(), work.right() - WIDTH + 1)
        maximum_y = max(work.top(), work.bottom() - self.height() + 1)
        x = min(max(self.x(), work.left()), maximum_x)
        y = min(max(self.y(), work.top()), maximum_y)
        distances = {"left": x - work.left(), "right": maximum_x - x,
                     "top": y - work.top(), "bottom": maximum_y - y}
        candidates = [edge for edge, distance in distances.items() if distance <= 12]
        if candidates:
            if len(candidates) > 1:
                delta = pointer - self._drag_origin_global
                axis = ("left", "right") if abs(delta.x()) > abs(delta.y()) else ("top", "bottom")
                candidates = [edge for edge in candidates if edge in axis] or candidates
            edge = min(candidates, key=lambda candidate: distances[candidate])
            self.set_dock_edge(edge)
            maximum_y = max(work.top(), work.bottom() - self.height() + 1)
            y = min(max(y, work.top()), maximum_y)
            if self.dock_edge == "left":
                x = work.left()
            elif self.dock_edge == "right":
                x = maximum_x
            elif self.dock_edge == "top":
                y = work.top()
            else:
                y = maximum_y
        else:
            self.set_dock_edge(None)
            maximum_y = max(work.top(), work.bottom() - self.height() + 1)
            y = min(max(y, work.top()), maximum_y)
            self.set_expansion_progress(1.0)  # Free positions keep their information visible.
        self.move(x, y)
        self._update_mask()
        self.update()
        local = self.mapFromGlobal(pointer)
        self._last_inside = self._visible_hit(local.x(), local.y())
        if self.dock_edge is not None and not self._last_inside and self._progress > .01:
            self._close_timer.start(700)

    def _perform_click(self, x: float, y: float) -> None:
        # Activation belongs to release, so a drag cannot accidentally copy.
        self.pinned = False
        self._reset_keyboard_focus()
        if self._progress < .9:
            self.expand()
            self.clearFocus()
        elif (index := self._ball_at(x, y)) >= 0:
            self._activate_ball(index)
            self.clearFocus()
        elif provider := self._provider_at(x, y):
            self.set_detail(provider)
            self.clearFocus()
        elif self._shell_target().contains(QPointF(x, y)):
            self.clearFocus()

    def _activate_ball(self, index: int) -> None:
        if index == 0:
            QApplication.clipboard().setText(SAMPLE_TEXT)
            success = QApplication.clipboard().text() == SAMPLE_TEXT
            self.copy_feedback = "已复制 · 需求澄清" if success else "复制失败 · 请重试"
            self._feedback_timer.start(1800)
        elif index == 3 and self.unread_reminder:
            self.acknowledge_reminder_demo()
            self._show_ball_tip(index, "演示提醒已查看")
        else:
            self._show_ball_tip(index, f"{BALL_NAMES[index]} · 后续阶段")
        self.update()

    def _focused_action_index(self) -> int | None:
        index = self.keyboard_ball - len(FOCUS_PROVIDERS)
        return index if 0 <= index < len(BALL_NAMES) else None

    def _focus_next(self, step: int) -> None:
        self.expand()
        count = len(FOCUS_PROVIDERS) + len(BALL_NAMES)
        self.keyboard_ball = (self.keyboard_ball + step) % count if self.keyboard_ball >= 0 else (0 if step > 0 else count - 1)
        self.pinned = True
        self.hover_ball = -1
        if self.keyboard_ball < len(FOCUS_PROVIDERS):
            self.set_detail(FOCUS_PROVIDERS[self.keyboard_ball])
            self.setAccessibleDescription(f"当前平台：{FOCUS_PROVIDERS[self.keyboard_ball]}。按回车或空格查看详情。")
        else:
            self.set_detail("")
            self.setAccessibleDescription(f"当前操作：{BALL_NAMES[self.keyboard_ball - len(FOCUS_PROVIDERS)]}。按回车或空格执行。")
        self.update()

    def _reset_keyboard_focus(self) -> None:
        self.keyboard_ball = -1
        self.setAccessibleDescription(self._default_accessible_description)

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.keyboard_ball in range(len(FOCUS_PROVIDERS)):
                self.expand()
                self.set_detail(FOCUS_PROVIDERS[self.keyboard_ball])
            elif (action := self._focused_action_index()) is not None:
                self.expand()
                self._activate_ball(action)
            elif self._progress < 0.9:
                self.expand()
            else:
                self.pinned = True
                self.set_detail("codex")
        elif key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            reverse = key == Qt.Key.Key_Backtab or bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            self._focus_next(-1 if reverse else 1)
        elif key == Qt.Key.Key_Escape:
            self.pinned = False
            self._reset_keyboard_focus()
            self.hover_ball = -1
            self.set_detail("")
            self.clearFocus()
            self._close_timer.start(700)
        elif key == Qt.Key.Key_M:
            self.reduced_motion = not self.reduced_motion
            if self.reduced_motion:
                self._quota_animation.stop()
                self._previous_sample = None
                self._quota_blend = 1.0
                self._reminder_animation.stop()
                self._reminder_pulse = 0.0
            self._update_mask()
            self.update()
        elif key == Qt.Key.Key_N:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.acknowledge_reminder_demo()
            else:
                self.trigger_reminder_demo()
        elif key == Qt.Key.Key_Q and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.close()
        elif Qt.Key.Key_1 <= key <= Qt.Key.Key_6:
            self._set_presentation(STATE_NAMES[key - Qt.Key.Key_1])
        elif key in (Qt.Key.Key_7, Qt.Key.Key_8, Qt.Key.Key_9, Qt.Key.Key_0):
            self._set_presentation("normal", {Qt.Key.Key_7: "abundant", Qt.Key.Key_8: "middle", Qt.Key.Key_9: "low", Qt.Key.Key_0: "unknown"}[key])
        elif key == Qt.Key.Key_R:
            self._set_presentation("normal", "baseline")
        elif key == Qt.Key.Key_B:
            self._five_at = self._now() + timedelta(hours=10, seconds=1)
            self._week_at = self._now() + timedelta(days=1, seconds=1)
            self.set_detail("codex")
            self.pinned = True
            self.update()
        elif key == Qt.Key.Key_Z:
            self._five_at = self._now() - timedelta(seconds=1)
            self.set_detail("codex")
            self.pinned = True
            self.update()
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        if self.keyboard_ball >= 0:
            self._reset_keyboard_focus()
            self.hover_ball = -1
            self.pinned = False
            self.set_detail("")
            self.update()
        if not self.pinned and not self._last_inside:
            self._close_timer.start(700)

    def paintEvent(self, event) -> None:
        start = time.perf_counter()
        if self.audit_layout:
            self.layout_issues.clear()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.GlobalColor.transparent)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        p.setPen(QPen(CONTOUR, CONTOUR_WIDTH))
        p.setBrush(PAPER)
        p.drawPath(self._shell_path())
        self._paint_dock_ball(p)
        self._paint_quota_handoff(p)
        if self._progress > .01:
            p.save()
            p.setClipPath(self._shell_path())
            dx, dy = self._content_offset()
            p.translate(dx, dy)
            self._paint_content(p)
            p.restore()
            self._paint_balls(p)
        p.end()
        self._frame_ms.append((time.perf_counter() - start) * 1000)
        if len(self._frame_ms) > 500:
            self._frame_ms = self._frame_ms[-500:]

    def _paint_dock_ball(self, p: QPainter) -> None:
        # Shell and dials are painted elsewhere. This slot holds only the
        # balance, benefit and reminder glyphs until leaf content takes over.
        alpha = 1 - ease((self._progress - .02) / .22)
        if alpha <= 0.01:
            return
        p.save()
        p.setOpacity(alpha)
        sample = self._sample()
        p.setFont(self._font(7.2, bold=True, numeric=True))
        p.setPen(MUTED if sample.deepseek_balance is None else self.palette.balance)
        edge = self._visual_edge()
        if edge == "right":
            yen_x, yen_y = DOCK_RING_X + 8, 161
        elif edge == "left":
            yen_x, yen_y = 16, 161
        else:
            yen_x = self._dock_center().x() - 3
            yen_y = self._dock_center().y() + (31 if edge == "top" else 28)
        p.drawText(QPointF(yen_x, yen_y), "¥")
        if sample.deepseek_balance is None:
            p.setPen(QPen(MUTED, 1.4))
            p.drawLine(QPointF(yen_x - 1, yen_y - 5), QPointF(yen_x + 7, yen_y - 8))
        self._paint_dock_benefits(p)
        if self.state == "error":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.palette.low)
            dock = self._dock_center()
            p.drawEllipse(QPointF(dock.x() - (23 if edge in ("right", "left") else 10), dock.y() - 24), 2, 2)
        if self.unread_reminder:
            self._paint_dock_reminder(p)
        p.restore()

    def _paint_dock_benefits(self, p: QPainter) -> None:
        sample = self._sample()
        edge = self._visual_edge()
        if edge in ("right", "left"):
            mark_x = DOCK_BENEFIT_X if edge == "right" else 3
            mark_positions = {"codex": (mark_x, 124), "glm": (mark_x, 146), "deepseek": (mark_x, 161)}
        else:
            center = self._dock_center()
            mark_x = center.x() + 8
            mark_positions = {"codex": (mark_x, center.y() - 6),
                              "glm": (mark_x, center.y() + 16),
                              "deepseek": (mark_x, center.y() + (31 if edge == "top" else 28))}
        for provider in ("codex", "glm"):
            mark_x, baseline = mark_positions[provider]
            mark = self._trust_mark(provider, sample)
            if mark:
                p.setFont(self._font(7.0, bold=True))
                p.setPen(INK if mark == "旧" else MUTED)
                p.drawText(QPointF(mark_x, baseline), mark)
            elif provider == "glm":
                p.setFont(self._font(7.0, bold=True))
                p.setPen(self.palette.benefit)
                p.drawText(QPointF(mark_x, baseline), "半")
        p.setFont(self._font(7.0, bold=True))
        mark_x, baseline = mark_positions["deepseek"]
        if self.state == "disconnected":
            p.setPen(INK)
            p.drawText(QPointF(mark_x, baseline), "断")
        elif sample.deepseek_balance is None:
            p.setPen(MUTED)
            p.drawText(QPointF(mark_x, baseline), "缺")
        else:
            p.setPen(self.palette.benefit)
            p.drawText(QPointF(mark_x, baseline), "半")

    def _draw_quota_dial(self, p: QPainter, rect: QRectF, percent: float | None, provider: str) -> None:
        track = QPen(RULE if percent is not None else MUTED, 2.4)
        track.setCapStyle(Qt.PenCapStyle.FlatCap)
        if percent is None:
            track.setDashPattern([1.15, 1.15])
        p.setPen(track)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(rect, 90 * 16, -360 * 16)
        if percent is None:
            return
        color = self._quota_color(provider, percent)
        fill = QPen(color, 3.05)
        fill.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(fill)
        if percent > 0:
            p.drawArc(rect, 90 * 16, -round(360 * 16 * percent / 100))
        if percent <= LOW_REMAINING:
            angle = math.radians(90 - 360 * percent / 100)
            endpoint = QPointF(rect.center().x() + rect.width() / 2 * math.cos(angle), rect.center().y() - rect.height() / 2 * math.sin(angle))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawRect(QRectF(endpoint.x() - 2.25, endpoint.y() - 2.25, 4.5, 4.5))

    def _draw_dock_window_label(self, p: QPainter, rect: QRectF, window: str | None) -> None:
        label = "H" if window == "5h" else "W" if window == "week" else "?"
        p.setFont(self._font(6.5, bold=True, numeric=True))
        p.setPen(MUTED if window is None else INK)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

    def _paint_quota_handoff(self, p: QPainter) -> None:
        """Draw each dial exactly once, from its dock slot to its leaf slot."""
        if self._progress >= .60 or self.reduced_motion and self._progress > .001:
            return
        travel = ease((self._progress - .08) / .44)
        opacity = 1 - ease((self._progress - .45) / .15)
        if opacity <= .01:
            return
        p.save()
        p.setOpacity(opacity)
        p.setFont(self._font(7, bold=True, numeric=True))
        sample = self._sample()
        for letter, provider in (("C", "codex"), ("G", "glm")):
            choice = tightest_provider_window(sample, provider)
            window = choice[0] if choice else None
            weekly = window == "week"
            end_x = (142 if provider == "codex" else 217) if weekly else (147 if provider == "codex" else 226)
            end_y = 193 if weekly else 167
            dx, dy = self._content_offset()
            end_x += dx
            end_y += dy
            dock_start = self._dock_dial_center(provider)
            start_x, start_y = dock_start.x(), dock_start.y()
            center_x = start_x + (end_x - start_x) * travel
            center_y = start_y + (end_y - start_y) * travel
            size = 17 + (2 if weekly else 19) * travel
            p.setPen(INK)
            letter_x = center_x + size / 2 + 1 if self._visual_edge() == "left" else center_x - size / 2 - 8
            p.drawText(QPointF(letter_x, center_y + 5.5), letter)
            dial_rect = QRectF(center_x - size / 2, center_y - size / 2, size, size)
            self._draw_quota_dial(p, dial_rect, self._graphic_value(provider, window) if window else None, provider)
            self._draw_dock_window_label(p, dial_rect, window)
        p.restore()

    def _paint_dock_reminder(self, p: QPainter) -> None:
        edge = self._visual_edge()
        if edge == "right":
            x, y = DOCK_X - 8, 96
        elif edge == "left":
            x, y = 16, 96
        elif edge == "top":
            # Keep the bell inside the cropped top circle, clear of the C dial
            # and its platform letter even at the peak of its 9 degree sway.
            x, y = WIDTH / 2 + 10, 4
        else:
            x, y = WIDTH / 2, self.height() - 65
        p.save()
        if not self.reduced_motion and self._reminder_animation.state() == QPropertyAnimation.State.Running:
            p.translate(x, y + 5)
            p.rotate(9 * math.sin(5 * math.pi * self._reminder_pulse) * (1 - self._reminder_pulse))
            p.translate(-x, -(y + 5))
        pen = QPen(self.palette.reminder, 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(x - 4, y, 8, 7), 0, 180 * 16)
        p.drawLine(QPointF(x - 4, y + 3), QPointF(x - 4, y + 7))
        p.drawLine(QPointF(x + 4, y + 3), QPointF(x + 4, y + 7))
        p.drawLine(QPointF(x - 5, y + 7), QPointF(x + 5, y + 7))
        p.drawPoint(QPointF(x, y + 9))
        p.restore()

    def _draw_quota_arc(self, p: QPainter, rect: QRectF, percent: float | None, provider: str, stroke_scale: float = 1.0) -> None:
        track = QPen(RULE if percent is not None else MUTED, (2.3 if percent is not None else 1.8) * stroke_scale)
        track.setCapStyle(Qt.PenCapStyle.FlatCap)
        if percent is None:
            track.setDashPattern([1.2, 1.4])
        p.setPen(track)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(rect, 90 * 16, 180 * 16)
        if percent is None:
            return
        color = self._quota_color(provider, percent)
        fill = QPen(color, 2.8 * stroke_scale)
        fill.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(fill)
        if percent > 0:
            p.drawArc(rect, 90 * 16, round(180 * 16 * percent / 100))
        angle = math.radians(90 + 180 * percent / 100)
        center = rect.center()
        endpoint = QPointF(center.x() + rect.width() / 2 * math.cos(angle), center.y() - rect.height() / 2 * math.sin(angle))
        if percent <= LOW_REMAINING:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            marker = 4.1 * stroke_scale
            p.drawRect(QRectF(endpoint.x() - marker / 2, endpoint.y() - marker / 2, marker, marker))

    def _font(self, size: float, bold: bool = False, numeric: bool = False) -> QFont:
        f = QFont("Bahnschrift" if numeric else "Microsoft YaHei UI")
        f.setPointSizeF(size)
        f.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
        if numeric:
            f.setStyleStrategy(QFont.StyleStrategy.PreferDefault)
        return f

    def _text(self, p: QPainter, x: float, y: float, content: str, size: float = 10, color: QColor = INK, bold: bool = False, numeric: bool = False, width: float = 0, alignment=Qt.AlignmentFlag.AlignLeft) -> None:
        font = self._font(size, bold, numeric)
        p.setFont(font)
        p.setPen(color)
        if self.audit_layout and self._progress > .99:
            dx, dy = self._content_offset()
            bounds = QFontMetricsF(font).boundingRect(content).translated(x + dx, y + dy)
            corners = (QPointF(bounds.left(), bounds.top()), QPointF(bounds.right(), bounds.top()),
                       QPointF(bounds.left(), bounds.bottom()), QPointF(bounds.right(), bounds.bottom()))
            if any(not self._shell_target().contains(point) for point in corners):
                self.layout_issues.append(f"{content!r} at ({x},{y}) bounds {bounds}")
        if width:
            p.drawText(QRectF(x, y - size * 1.15, width, size * 1.55), alignment | Qt.AlignmentFlag.AlignVCenter, content)
        else:
            p.drawText(QPointF(x, y), content)

    def _rule(self, p: QPainter, x1: float, y: float, x2: float) -> None:
        p.setPen(QPen(RULE, 0.8))
        p.drawLine(QPointF(x1, y), QPointF(x2, y))

    def _paint_content(self, p: QPainter) -> None:
        p.save()
        if not self.reduced_motion:
            p.setOpacity(p.opacity() * ease((self._progress - .28) / .18))
        self._paint_time_slot(p)
        self._rule(p, 94, 121, 263)
        p.restore()
        self._paint_summary(p)
        p.save()
        if not self.reduced_motion:
            p.setOpacity(p.opacity() * ease((self._progress - .62) / .18))
        self._rule(p, 98, 205, 257)
        self._paint_balance(p)
        p.restore()

    def _paint_time_slot(self, p: QPainter) -> None:
        now = self._now()
        title_x = 145 if self._visual_edge() == "left" else 95
        if self.copy_feedback:
            success = self.copy_feedback.startswith("已复制")
            self._text(p, title_x, 56, "复制完成" if success else "复制失败", 9.6, self.palette.action if success else self.palette.low, True)
            self._text(p, 105 if self._visual_edge() == "left" else 95, 85, "需求澄清" if success else "剪贴板暂不可用", 13.5, INK, True)
            self._text(p, 95, 108, "已写入剪贴板 · Ctrl+V 粘贴" if success else "请稍后重试", 9, MUTED)
            return
        if (action := self._focused_action_index()) is not None:
            name = BALL_NAMES[action]
            hint = ("Enter / 空格复制" if action == 0 else
                    "Enter / 空格查看提醒" if action == 3 and self.unread_reminder else
                    "Enter / 空格查看说明")
            self._text(p, title_x, 56, f"操作 {action + 1} / {len(BALL_NAMES)}", 9.2, MUTED, True)
            self._text(p, 105 if self._visual_edge() == "left" else 95, 84, name, 11.8, INK, True)
            self._text(p, 95, 107, hint, 9, MUTED)
            return
        if self.state in ("loading", "empty", "error"):
            message = {"loading": "正在读取额度", "empty": "尚无额度数据", "error": "读取失败"}[self.state]
            self._text(p, title_x, 58, "对照叶 / DEMO", 8.8, MUTED)
            self._text(p, 105 if self._visual_edge() == "left" else 95, 85, message, 12, INK, True)
            self._text(p, 95, 108, {"loading": "请稍候", "empty": "连接账户后显示", "error": "尚无成功快照"}[self.state], 9.3, MUTED)
            if self.state == "loading":
                self._rule(p, 95, 115, 146)
            return
        blend = self._detail_opacity
        outgoing = max(0.0, min(1.0, (.55 - blend) / .55))
        incoming = max(0.0, min(1.0, (blend - .45) / .55))
        if outgoing > .01:
            p.save()
            p.setOpacity(p.opacity() * outgoing)
            self._paint_time_content(p, self._previous_detail, now)
            p.restore()
        if incoming > .01:
            p.save()
            p.setOpacity(p.opacity() * incoming)
            self._paint_time_content(p, self.detail, now)
            p.restore()

    def _paint_time_content(self, p: QPainter, detail: str, now: datetime) -> None:
        sample = self._sample()
        left = self._visual_edge() == "left"
        title_x = 145 if left else 95
        five_label_x = 105 if left else 95
        five_countdown_x = DETAIL_COUNTDOWN_X + (8 if left else 0)
        meta_x = DETAIL_META_X + (52 if left else 0)
        if detail == "deepseek":
            self._text(p, title_x, 56, "DeepSeek", 9.5, self.palette.balance, True)
            self._text(p, 108 if left else 95, 82, "余额快照未提供" if sample.deepseek_balance is None else "人民币 · API 按量计费", 10.2, INK, True)
            self._text(p, 95, 105, "更新时间未提供" if sample.deepseek_balance is None else "更新 02:09 · 常态半价", 9, MUTED)
            return
        if detail == "glm":
            self._text(p, title_x, 54, "GLM", 9.5, self.palette.glm, True)
            self._text(p, meta_x, 54, "保留 02:09" if self._provider_stale("glm") else "更新 02:09", 9, MUTED)
            self._text(p, five_label_x, 80, f"5h {self._glm_five_at:%H:%M}" if sample.glm_5h is not None else "5h", 9, MUTED)
            self._paint_countdown(p, "glm5", present_countdown(self._glm_five_at, now) if sample.glm_5h is not None else None, five_countdown_x, 80, 10)
            self._text(p, 95, 106, "周 未提供", 9, MUTED)
            self._text(p, 163, 106, "恢复时间未提供", 9, MUTED)
            return
        if detail == "codex":
            self._text(p, title_x, 54, "Codex", 9.5, self.palette.codex, True)
            self._text(p, meta_x, 54, "更新 02:09", 9, MUTED)
            self._text(p, five_label_x, 80, f"5h {self._five_at:%H:%M}" if sample.codex_5h is not None else "5h", 9, MUTED)
            self._paint_countdown(p, "codex5", present_countdown(self._five_at, now) if sample.codex_5h is not None else None, five_countdown_x, 80, 10)
            self._text(p, 95, 106, f"周 {self._week_at:%m/%d}" if sample.codex_week is not None else "周", 9, MUTED)
            self._paint_countdown(p, "codexw", present_countdown(self._week_at, now) if sample.codex_week is not None else None, DETAIL_COUNTDOWN_X, 106, 10)
            return
        lowest = lowest_remaining(sample, include_week=True)
        if lowest is None:
            self._text(p, title_x, 56, "四窗额度未知", 9.6, MUTED, True)
            self._text(p, 103 if left else 95, 87, "未知", 13.2, INK, True)
            self._text(p, 95, 107, "Codex / GLM 均未提供额度", 8.8, MUTED)
            return
        provider, window, value = lowest
        recovery_at = {
            ("codex", "5h"): self._five_at,
            ("codex", "week"): self._week_at,
            ("glm", "5h"): self._glm_five_at,
            ("glm", "week"): self._glm_week_at,
        }[(provider, window)]
        default = present_countdown(recovery_at, now)
        label = "Codex" if provider == "codex" else "GLM"
        window_label = "5h" if window == "5h" else "周"
        limited = self.state == "stale" or any(sample.percent(name, span) is None
                                                 for name in ("codex", "glm") for span in ("5h", "week"))
        self._text(p, title_x, 56, f"{'已知' if limited else '最低'} · {label} {window_label}", 9.6, self._provider_color(provider), True)
        self._text(p, 103 if left else 95, 87, f"{value}%", 13.2, self._quota_color(provider, value), True, numeric=True)
        self._paint_countdown(p, f"default-{provider}-{window}", default, 147, 87, 9.8)
        stamp = "保留 02:09" if self._provider_stale(provider) else "更新 02:09"
        if default and default.status == "awaiting_confirmation":
            self._text(p, 95, 107, "待确认 · 更新后核验", 8.8, self.palette.low)
        elif default is None:
            self._text(p, 95, 107, f"{'周恢复' if window == 'week' else '恢复'}未提供 · {stamp}", 8.8, MUTED)
        else:
            verb = "恢复" if provider == "codex" else "补回"
            when = f"{recovery_at:%H:%M}" if window == "5h" else f"{recovery_at:%m/%d %H:%M}"
            suffix = f" · {stamp}" + (" · 示例" if window == "5h" else "")
            self._text(p, 95, 107, f"{verb} {when}{suffix}", 8.8, MUTED)

    def _paint_countdown(self, p: QPainter, key: str, current: Countdown | None, x: float, y: float, point_size: float) -> None:
        if current is None:
            self._text(p, x, y, "未提供", 9, MUTED)
            return
        previous = self._countdown_previous.get(key)
        if previous != current:
            if previous and self._progress > .95 and not self.reduced_motion:
                self._countdown_motion[key] = (previous, current, time.monotonic())
            self._countdown_previous[key] = current
        motion = self._countdown_motion.get(key)
        elapsed = time.monotonic() - motion[2] if motion else 999
        duration = .18 if motion and motion[0].mode != motion[1].mode else .16
        if elapsed >= duration:
            self._countdown_motion.pop(key, None)
            motion = None
        slot_width = 42 if point_size > 11 else 32
        if motion and motion[0].mode != motion[1].mode:
            progress = ease(elapsed / duration)
            base_opacity = p.opacity()
            p.save()
            p.setOpacity(base_opacity * (1 - progress))
            self._draw_countdown_fields(p, motion[0], x, y - 3 * progress, point_size, slot_width)
            p.restore()
            p.save()
            p.setOpacity(base_opacity * progress)
            self._draw_countdown_fields(p, current, x, y + 3 * (1 - progress), point_size, slot_width)
            p.restore()
            return
        self._draw_countdown_fields(p, current, x, y, point_size, slot_width, motion, elapsed / duration if motion else 1)

    def _draw_countdown_fields(self, p: QPainter, countdown: Countdown, x: float, y: float, point_size: float, slot_width: int, motion=None, fraction: float = 1) -> None:
        p.setFont(self._font(point_size, True, True))
        p.setPen(INK)
        digit_width = 10 if point_size > 11 else 8
        unit_x = 22 if point_size > 11 else 18
        progress = ease(fraction)
        for field_index, (value, unit) in enumerate(countdown.fields):
            slot_x = x + field_index * slot_width
            if self.audit_layout and self._progress > .99:
                dx, dy = self._content_offset()
                unit_font = self._font(point_size - .7)
                digit_font = self._font(point_size, True, True)
                right = max(slot_x + digit_width + QFontMetricsF(digit_font).horizontalAdvance("9"),
                            slot_x + unit_x + QFontMetricsF(unit_font).horizontalAdvance(unit))
                top = y - max(QFontMetricsF(unit_font).ascent(), QFontMetricsF(digit_font).ascent())
                bottom = y + max(QFontMetricsF(unit_font).descent(), QFontMetricsF(digit_font).descent())
                if any(not self._shell_target().contains(QPointF(px + dx, py + dy)) for px in (slot_x, right) for py in (top, bottom)):
                    self.layout_issues.append(f"countdown {value}{unit} at ({slot_x},{y}) to {right:.1f}")
            padded = value.rjust(2)
            previous_padded = motion[0].fields[field_index][0].rjust(2) if motion else padded
            for digit_index, digit in enumerate(padded):
                old = previous_padded[digit_index]
                if digit == old or not motion or digit == " " and old == " ":
                    if digit != " ":
                        p.drawText(QPointF(slot_x + digit_index * digit_width, y), digit)
                    continue
                p.save()
                p.setClipRect(QRectF(slot_x + digit_index * digit_width - 1, y - 17, digit_width + 3, 21))
                base_opacity = p.opacity()
                if old != " ":
                    p.setOpacity(base_opacity * (1 - progress))
                    p.drawText(QPointF(slot_x + digit_index * digit_width, y - 5 * progress), old)
                if digit != " ":
                    p.setOpacity(base_opacity * progress)
                    p.drawText(QPointF(slot_x + digit_index * digit_width, y + 5 * (1 - progress)), digit)
                p.restore()
            p.setFont(self._font(point_size - .7, False))
            p.setPen(MUTED)
            p.drawText(QPointF(slot_x + unit_x, y), unit)
            p.setFont(self._font(point_size, True, True))
            p.setPen(INK)

    def _paint_summary(self, p: QPainter) -> None:
        sample = self._sample()
        codex_selected = self.detail == "codex"
        glm_selected = self.detail == "glm"
        p.save()
        if not self.reduced_motion:
            p.setOpacity(p.opacity() * ease((self._progress - .44) / .28))
        self._text(p, 95, 141, "剩余", 8.5, MUTED)
        self._text(p, 129, 141, "Codex", 9.5, self.palette.codex if codex_selected else INK, True)
        self._text(p, 209, 141, "GLM", 9.5, self.palette.glm if glm_selected else INK, True)
        codex_mark = self._trust_mark("codex", sample)
        glm_mark = self._trust_mark("glm", sample)
        if codex_mark:
            self._text(p, 177, 141, "旧值" if codex_mark == "旧" else "缺项", 8.1, MUTED)
        if glm_mark:
            self._text(p, 244, 141, "旧值" if glm_mark == "旧" else "缺项", 8.1, MUTED)
        else:
            self._paint_benefit_word(p, 244, 141, "耗")
        if self.keyboard_ball in (0, 1):
            left, right = (129, 178) if self.keyboard_ball == 0 else (209, 249)
            p.setPen(QPen(self.palette.codex if self.keyboard_ball == 0 else self.palette.glm, 1.5))
            p.drawLine(QPointF(left, 145), QPointF(right, 145))
        p.restore()
        p.save()
        if not self.reduced_motion:
            p.setOpacity(p.opacity() * ease((self._progress - .50) / .20))
        for provider, x in (("codex", 129), ("glm", 208)):
            five, week = (sample.percent(provider, window) for window in ("5h", "week"))
            if week is not None and week <= LOW_REMAINING and (five is None or five > LOW_REMAINING):
                p.save()
                p.setOpacity(p.opacity() * .65)
                self._draw_quota_arc(p, QRectF(x, 149, 36, 36), self._graphic_value(provider, "5h"), provider, 1.5)
                p.restore()
            else:
                self._draw_quota_arc(p, QRectF(x, 149, 36, 36), self._graphic_value(provider, "5h"), provider, 1.5)
        p.restore()
        p.save()
        if not self.reduced_motion:
            p.setOpacity(p.opacity() * ease((self._progress - .65) / .20))
        self._text(p, 95, 172, "5h", 9.2, MUTED, numeric=True)
        self._text(p, 95, 197, "周", 9.2, MUTED)
        for provider, rail_x, five_x, week_x in (("codex", 129, 151, 159), ("glm", 204, 232, 234)):
            five = sample.percent(provider, "5h")
            week = sample.percent(provider, "week")
            five_low = five is not None and five <= LOW_REMAINING
            week_low = week is not None and week <= LOW_REMAINING
            five_color = MUTED if week_low and not five_low else self._quota_color(provider, five) if five is not None else INK
            week_color = MUTED if five_low and not week_low else self._quota_color(provider, week) if week_low else INK
            self._text(p, five_x, 172, f"{five}%" if five is not None else "未知", 11.1 if five is not None else 8.2, five_color, True, numeric=five is not None)
            self._text(p, week_x, 197, f"{week}%" if week is not None else "未知", 10.1 if week_low else 9.3 if week is not None else 8.2, week_color, True, numeric=week is not None)
            if five_low and not week_low:
                p.save()
                p.setOpacity(p.opacity() * .65)
                self._draw_quota_rail(p, rail_x, 194, 27, self._graphic_value(provider, "week"), provider)
                p.restore()
            else:
                self._draw_quota_rail(p, rail_x, 194, 27, self._graphic_value(provider, "week"), provider)
            critical = [(window, value) for window, value in (("5h", five), ("week", week))
                        if value is not None and value <= LOW_REMAINING]
            if critical:
                window, _ = min(critical, key=lambda pair: pair[1])
                self._paint_risk_bracket(p, 122 if provider == "codex" else 197, 168 if window == "5h" else 193)
        p.restore()

    def _paint_risk_bracket(self, p: QPainter, x: float, y: float) -> None:
        """The same fixed-column pointer marks whichever window constrains use."""
        p.save()
        p.setPen(QPen(self.palette.low, 2.2))
        p.drawLine(QPointF(x, y - 6), QPointF(x, y + 6))
        p.drawLine(QPointF(x, y - 6), QPointF(x + 3.5, y - 6))
        p.drawLine(QPointF(x, y + 6), QPointF(x + 3.5, y + 6))
        p.restore()

    def _draw_quota_rail(self, p: QPainter, x: float, y: float, width: float, percent: float | None, provider: str = "codex") -> None:
        base = QPen(RULE if percent is not None else MUTED, 2.5 if percent is not None else 1.4)
        base.setCapStyle(Qt.PenCapStyle.RoundCap)
        if percent is None:
            base.setDashPattern([2, 2.5])
        p.setPen(base)
        p.drawPath(self._vein_path(x, y, width, 1))
        if percent is None:
            return
        fraction = percent / 100
        end = x + width * fraction
        end_y = y + 2.2 * math.sin(math.pi * fraction)
        color = self._quota_color(provider, percent)
        fill = QPen(color, 4.5)
        fill.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.save()
        if not self.reduced_motion:
            p.setOpacity(p.opacity() * ease((self._progress - 0.3) / 0.6))
        p.setPen(fill)
        if percent > 0:
            p.drawPath(self._vein_path(x, y, width, fraction))
        if percent <= LOW_REMAINING:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawRect(QRectF(end - 2.5, end_y - 3.2, 5, 6.4))
            p.setBrush(Qt.BrushStyle.NoBrush)
        p.restore()

    def _vein_path(self, x: float, y: float, width: float, fraction: float) -> QPainterPath:
        path = QPainterPath(QPointF(x, y))
        steps = max(1, round(24 * fraction))
        for step in range(1, steps + 1):
            t = fraction * step / steps
            path.lineTo(QPointF(x + width * t, y + 2.2 * math.sin(math.pi * t)))
        return path

    def _paint_balance(self, p: QPainter) -> None:
        sample = self._sample()
        self._text(p, 100, 219, "DeepSeek", 9.4, self.palette.balance if self.detail == "deepseek" else INK)
        if self.keyboard_ball == 2:
            p.setPen(QPen(self.palette.balance, 1.5))
            p.drawLine(QPointF(100, 223), QPointF(159, 223))
        if self.state == "disconnected":
            self._text(p, 168 if self._visual_edge() == "left" else 167, 219, "未连接", 9.5, self.palette.low)
        elif sample.deepseek_balance is None:
            self._text(p, 168 if self._visual_edge() == "left" else 167, 219, "余额未知", 9.5, MUTED)
        else:
            self._text(p, 168 if self._visual_edge() == "left" else 171, 219, sample.deepseek_balance, 10.8, self.palette.balance, True, numeric=True)
        if sample.deepseek_balance is not None:
            self._paint_benefit_word(p, 218 if self._visual_edge() == "left" else 230, 219, "价")

    def _paint_benefit_word(self, p: QPainter, x: float, y: float, suffix: str) -> None:
        """Render both leading 半 glyphs with identical font and pixel phase."""
        size = 8.1
        self._text(p, x, y, "半", size, self.palette.benefit)
        suffix_x = x + QFontMetricsF(self._font(size)).horizontalAdvance("半")
        self._text(p, suffix_x, y, suffix, size, self.palette.benefit)

    def _paint_balls(self, p: QPainter) -> None:
        for index in range(5):
            progress = self._ball_progress(index)
            if progress <= 0.01:
                continue
            center = self._ball_center(index)
            p.save()
            p.setOpacity(progress)
            p.translate(center)
            scale = 1 if self.reduced_motion else 0.88 + 0.12 * progress
            confirmed = index == 0 and bool(self.copy_feedback)
            if self.hover_ball == index or self.keyboard_ball == index + 3 or confirmed:
                scale *= 1.04
            p.scale(scale, scale)
            selected = self.hover_ball == index or self.keyboard_ball == index + 3 or confirmed
            fill = self.palette.low if confirmed and self.copy_feedback.startswith("复制失败") else self.palette.reminder if index == 3 and self.unread_reminder else self.palette.action
            p.setPen(QPen(fill if selected else CONTOUR, CONTOUR_WIDTH))
            p.setBrush(fill if selected else PAPER)
            p.drawEllipse(QPointF(0, 0), 15.5, 15.5)
            if self.keyboard_ball == index + 3:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(0, 0), 18, 18)
            if index == 3 and self.unread_reminder and not self.reduced_motion and self._reminder_animation.state() == QPropertyAnimation.State.Running:
                p.save()
                p.rotate(9 * math.sin(5 * math.pi * self._reminder_pulse) * (1 - self._reminder_pulse))
                self._paint_icon(p, index, PAPER if selected else INK)
                p.restore()
            else:
                self._paint_icon(p, index, PAPER if selected else INK)
            if index == 3 and self.unread_reminder:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(PAPER if selected else INK)
                p.drawEllipse(QPointF(10, -10), 2.2, 2.2)
            p.restore()

    def _paint_icon(self, p: QPainter, index: int, color: QColor) -> None:
        pen = QPen(color, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        if index == 0 and self.copy_feedback:
            if self.copy_feedback.startswith("已复制"):
                p.drawLine(QPointF(-7, 0), QPointF(-2, 5))
                p.drawLine(QPointF(-2, 5), QPointF(8, -6))
            else:
                p.drawLine(QPointF(0, -7), QPointF(0, 2))
                p.drawEllipse(QPointF(0, 7), 1, 1)
            return
        if index in (0, 1):
            if index == 0:
                p.drawRoundedRect(QRectF(-8, -6, 11, 13), 2, 2)
                p.drawRoundedRect(QRectF(-3, -9, 11, 13), 2, 2)
            else:
                p.drawLine(QPointF(-8, -6), QPointF(7, -6))
                p.drawLine(QPointF(-8, -1), QPointF(5, -1))
                p.drawLine(QPointF(-8, 4), QPointF(2, 4))
                p.drawLine(QPointF(4, 5), QPointF(7, 8))
        elif index == 2:
            p.setBrush(color)
            for x in (-6, 0, 6):
                p.drawEllipse(QPointF(x, 0), 1.5, 1.5)
        elif index == 3:
            path = QPainterPath(QPointF(-6, 5))
            path.lineTo(QPointF(-4, 3))
            path.lineTo(QPointF(-4, -3))
            path.cubicTo(QPointF(-4, -10), QPointF(4, -10), QPointF(4, -3))
            path.lineTo(QPointF(4, 3))
            path.lineTo(QPointF(6, 5))
            path.closeSubpath()
            p.drawPath(path)
            p.drawLine(QPointF(-7, 5), QPointF(7, 5))
            p.drawEllipse(QPointF(0, 8), 1, 1)
        else:
            p.drawEllipse(QPointF(0, 0), 5.5, 5.5)
            p.drawEllipse(QPointF(0, 0), 2, 2)
            for a in range(0, 360, 45):
                radians = math.radians(a)
                p.drawLine(QPointF(math.cos(radians) * 7.4, math.sin(radians) * 7.4), QPointF(math.cos(radians) * 9.4, math.sin(radians) * 9.4))

    def frame_metrics(self) -> dict[str, float]:
        if not self._frame_ms:
            return {"frames": 0, "p95_ms": 0}
        samples = sorted(self._frame_ms)
        return {"frames": len(samples), "p95_ms": round(samples[math.ceil(len(samples) * .95) - 1], 3)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", choices=STATE_NAMES, default="normal")
    parser.add_argument("--scenario", choices=tuple(SCENARIOS), default="baseline")
    parser.add_argument("--expanded", action="store_true")
    parser.add_argument("--detail", choices=("codex", "glm", "deepseek"), default="")
    parser.add_argument("--reduced-motion", action="store_true")
    parser.add_argument("--reminder-demo", action="store_true", help="Show an unread reminder cue without scheduling")
    parser.add_argument("--scale-factor", type=float, help="Qt scale multiplier for DPI review (native display is 150%%)")
    parser.add_argument("--capture", type=Path, help="Save one rendered frame from the live Qt window after startup")
    args = parser.parse_args()
    if args.scale_factor:
        os.environ["QT_SCALE_FACTOR"] = str(args.scale_factor)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("对照叶 Visual Prototype")
    app.setStyleSheet("QToolTip { color: #1e2119; background: #f5f2e9; border: 1px solid #9ca184; padding: 4px 6px; font: 10pt 'Microsoft YaHei UI'; }")
    widget = LeafPrototype(args.state, args.expanded or bool(args.detail), args.detail, args.reduced_motion, args.scenario)
    if args.reminder_demo:
        widget.trigger_reminder_demo()
    if args.capture:
        widget._pulse.stop()  # Keep scripted review captures independent of the real cursor position.
    screen = app.primaryScreen()
    work = screen.availableGeometry()
    widget.move(work.x() + work.width() - WIDTH, work.y() + max(34, (work.height() - HEIGHT) // 3))
    widget.show()
    if args.capture:
        def capture():
            args.capture.parent.mkdir(parents=True, exist_ok=True)
            widget.grab().save(str(args.capture))
            app.quit()
        QTimer.singleShot(700, capture)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
