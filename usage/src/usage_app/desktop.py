"""Native desktop lifecycle around the frozen leaf: tray, pin and safe placement."""
from __future__ import annotations

import ctypes
import hashlib
import html
import os
from ctypes import wintypes
from dataclasses import replace
from pathlib import Path
from typing import Callable, cast

from PySide6.QtCore import QAbstractAnimation, QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCloseEvent, QContextMenuEvent, QCursor, QEnterEvent, QFontMetricsF, QIcon, QKeyEvent, QMouseEvent, QMoveEvent, QPainter, QPainterPath, QPen, QPixmap, QResizeEvent, QScreen
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QToolTip

from main import CONTOUR, DOCK_RADIUS, INK, MUTED, OLIVE, PAPER, WIDTH, ease
from .account_ui import AccountPage
from .autostart import Autostart
from .desktop_geometry import Edge, Monitor, Placement, Rect, capture_placement, exterior_edge, nearest_dock
from .desktop_settings import DesktopSettings, DesktopSettingsStore
from .icons import paint_snippet_icon
from .reminder_service import ReminderService
from .reminder_ui import ReminderPage
from .reminders import Occurrence
from .runtime import UsageRuntime
from .snippet_service import CopyResult, SnippetService
from .snippets import FAVORITE_SLOTS
from .storage import StorageError
from .text_ui import MoreTexts, SnippetSettings
from .widget import LiveLeaf
from .windows_monitors import physical_monitor_rects
from .window_ui import WindowPage

MENU_STYLE = """
QMenu { color: #1e2119; background: #f5f2e9; border: 1px solid #9fa48f; padding: 5px; font: 10pt 'Microsoft YaHei UI'; }
QMenu::item { padding: 6px 26px 6px 20px; }
QMenu::item:selected { color: #f5f2e9; background: #58623d; }
QMenu::separator { height: 1px; background: #c9c9b9; margin: 5px 8px; }
"""


def screen_key(screen: QScreen) -> str:
    serial = screen.serialNumber()
    return f"{screen.manufacturer()}:{screen.model()}:{serial}" if serial else screen.name()


def screen_monitor(screen: QScreen) -> Monitor:
    full, work = screen.geometry(), screen.availableGeometry()
    return Monitor(screen_key(screen), Rect(full.x(), full.y(), full.width(), full.height()),
                   Rect(work.x(), work.y(), work.width(), work.height()), physical_monitor_rects().get(screen.name()))


def tray_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(size / 24, size / 24)
        path = QPainterPath(QPointF(3, 17))
        path.cubicTo(1, 6, 12, 0, 22, 5)
        path.cubicTo(24, 15, 14, 24, 3, 17)
        painter.setPen(QPen(CONTOUR, 1.2))
        painter.setBrush(PAPER)
        painter.drawPath(path)
        painter.setPen(QPen(OLIVE, 2))
        painter.drawArc(QRectF(5, 5, 14, 14), 45 * 16, 240 * 16)
        painter.setPen(QPen(INK, 1.2))
        painter.drawLine(QPointF(12, 12), QPointF(18, 9))
        painter.end()
        icon.addPixmap(pixmap)
    return icon


class SingleInstance:
    def __init__(self, data_dir: Path):
        identity = str(data_dir.resolve()).casefold().encode("utf-8")
        self.name = "duizhaoye-" + hashlib.sha256(identity).hexdigest()[:24]
        self.server = QLocalServer()
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)

    def acquire(self) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self.name)
        if socket.waitForConnected(200):
            socket.write(b"restore\n")
            socket.waitForBytesWritten(200)
            confirmed = socket.waitForReadyRead(1000) and socket.readLine().data() == b"ok\n"
            socket.disconnectFromServer()
            if not confirmed:
                raise StorageError("Existing instance did not confirm restore; no second instance was started")
            return False
        if not self.server.listen(self.name):
            raise StorageError("Another instance is starting; please retry")
        return True

    def on_restore(self, callback: Callable[[], None]) -> None:
        # Bound QObject slots are retained by Qt until server teardown.
        def connected() -> None:
            while self.server.hasPendingConnections():
                socket = self.server.nextPendingConnection()
                def consume(socket: QLocalSocket = socket) -> None:
                    if socket.bytesAvailable() > 32:
                        socket.disconnectFromServer()
                        return
                    if not socket.canReadLine():
                        return
                    if socket.readLine().data() == b"restore\n":
                        callback()
                        socket.write(b"ok\n")
                        socket.flush()
                    socket.disconnectFromServer()
                socket.readyRead.connect(consume)
                socket.disconnected.connect(socket.deleteLater)
                if socket.bytesAvailable():
                    consume()
        self.server.newConnection.connect(connected)


class DesktopLeaf(LiveLeaf):
    resumed = Signal()

    def __init__(self, runtime: UsageRuntime, *, reduced_motion: bool = False) -> None:
        self._ready_desktop = False
        self._restoring = False
        self._explicit_pin = False
        self._menu_open = False
        self._quitting = False
        self._auxiliary_open = False
        self._visible_panels: set[str] = set()
        self._copy_ball: int | None = None
        self._copy_result: CopyResult | None = None
        self.text_settings: SnippetSettings | None = None
        self.more_texts: MoreTexts | None = None
        self._settings = DesktopSettingsStore(runtime.data_dir)
        self.startup = Autostart(runtime.data_dir)
        preferences = self._settings.load()
        super().__init__(runtime, reduced_motion=reduced_motion or preferences.reduced_motion)
        self.snippets = SnippetService(runtime.data_dir, self)
        self.snippets.changed.connect(self.update)
        self.snippets.copied.connect(self._copied)
        self.snippets.error.connect(self._storage_problem)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowIcon(tray_icon())
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.save_placement)
        self._screen_timer = QTimer(self)
        self._screen_timer.setSingleShot(True)
        self._screen_timer.timeout.connect(self.restore_current)
        self._saved = preferences.placement
        self._ready_desktop = True
        self.apply_placement(preferences.placement)
        app = cast(QApplication, QApplication.instance())
        app.screenAdded.connect(self._screen_added)
        app.screenRemoved.connect(lambda screen: self._screen_timer.start(120))
        for screen in app.screens():
            self._screen_added(screen, schedule=False)
        self.resumed.connect(self.runtime.refresh_now)
        self._menu = self._make_menu()
        self.tray = QSystemTrayIcon(tray_icon(), self)
        self.tray.setToolTip("usage · 额度、快捷文本与每日提醒")
        self.tray.setContextMenu(self._menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()
        self.reminders = ReminderService(runtime.data_dir, self)
        self.reminders.changed.connect(self._reminder_changed)
        self.reminders.due.connect(self._notify_reminders)
        self.reminders.error.connect(self._storage_problem)
        self.resumed.connect(self.reminders.poll)
        self._reminder_changed()

    def _reminder_changed(self) -> None:
        self.unread_reminder = bool(self.reminders.unread)
        self.update()

    def _notify_reminders(self, occurrences: tuple[Occurrence, ...]) -> None:
        self.trigger_reminder_demo()  # Reuse the frozen event cue with actual due data.
        if self.tray.isVisible() and QSystemTrayIcon.supportsMessages():
            message = "\n".join(item.title for item in occurrences)
            if len(message) > 180:
                message = message[:170] + f"… 共 {len(occurrences)} 项"
            self.tray.showMessage("usage · 每日提醒", message, QSystemTrayIcon.MessageIcon.Information, 6000)
            self.reminders.submitted(occurrences)

    def _make_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        menu.setStyleSheet(MENU_STYLE)
        menu.aboutToShow.connect(self._menu_started)
        menu.aboutToHide.connect(self._menu_finished)
        menu.addAction("显示浮窗", self.restore_from_tray)
        self._pin_action = menu.addAction("固定展开  Ctrl+P")
        self._pin_action.setCheckable(True)
        self._pin_action.setChecked(self._explicit_pin)
        self._pin_action.toggled.connect(self.set_explicit_pin)
        menu.addAction("重新读取额度  R", self.runtime.refresh_now)
        menu.addAction("管理快捷文本", self.open_text_settings)
        menu.addAction("更多文本", self.open_more_texts)
        menu.addAction("每日提醒", self.open_reminders)
        menu.addAction("回到主屏右侧", self.reset_placement)
        menu.addSeparator()
        self._motion_action = menu.addAction("减少动态效果  M")
        self._motion_action.setCheckable(True)
        self._motion_action.setChecked(self.reduced_motion)
        self._motion_action.toggled.connect(self.set_reduced_motion)
        menu.addAction("隐藏到托盘", self.hide_to_tray)
        menu.addSeparator()
        menu.addAction("退出usage", self.quit_app)
        return menu

    def _menu_started(self) -> None:
        self._menu_open = True
        self._open_timer.stop()
        self._close_timer.stop()
        QToolTip.hideText()

    def _menu_finished(self) -> None:
        self._menu_open = False
        if self.keyboard_ball < 0:
            self.clearFocus()
        self._pulse.start(32)
        self._close_timer.start(700)

    def _auxiliary_visibility(self, panel: str, visible: bool) -> None:
        if visible:
            self._visible_panels.add(panel)
        else:
            self._visible_panels.discard(panel)
        self._auxiliary_open = bool(self._visible_panels)
        if self._auxiliary_open:
            self._close_timer.stop()
            self._hover_timer.stop()
            self._reset_keyboard_focus()
            self.pinned = self._explicit_pin
            QToolTip.hideText()
        else:
            self.clearFocus()
            self._pulse.start(32)
            self._close_timer.start(700)

    def open_text_settings(self) -> None:
        self._open_settings("texts")

    def open_reminders(self) -> None:
        self._open_settings("reminders")

    def _open_settings(self, section: str) -> None:
        if self.more_texts:
            self.more_texts.hide()
        if self.text_settings is None:
            self.text_settings = SnippetSettings(self.snippets)
            page = ReminderPage(self.reminders)
            self.text_settings.add_section("reminders", "每日提醒", "安排每天的提醒", "按本机时间安排事项。应用运行且电脑处于唤醒状态时生效。", page)
            self.text_settings.add_section("accounts", "账户", "连接你的三个平台", "额度和余额来自官方只读查询，每个平台独立连接。", AccountPage(self.runtime, self.theme))
            window_page = WindowPage(reduced_motion=self.reduced_motion, pinned=self._explicit_pin, startup=self.startup,
                                     apply=self._apply_window_behaviour, reset=self.reset_placement,
                                     snapshot=lambda: (self.reduced_motion, self._explicit_pin))
            self.text_settings.add_section("window", "窗口行为", "把usage放在顺手的位置", "四边自动贴靠，位置与显示方式随你保存。", window_page)
        # The independent editor needs no leaf anchor/hover lock. Opening it
        # ends temporary keyboard navigation, while an explicit pin is retained.
        self._reset_keyboard_focus()
        self.pinned = self._explicit_pin
        self.clearFocus()
        self._pulse.start(32)
        self._close_timer.start(700)
        panel = self.text_settings
        panel.select_section(section)
        work = self.screen().availableGeometry()
        panel.resize(min(panel.width(), work.width() - 32), min(panel.height(), work.height() - 32))
        panel.move(work.x() + (work.width() - panel.width()) // 2, work.y() + (work.height() - panel.height()) // 2)
        panel.show()
        panel.raise_()
        panel.activateWindow()

    def open_more_texts(self) -> None:
        self._copy_ball = None
        if self.more_texts is None:
            self.more_texts = MoreTexts(self.snippets, self.open_text_settings, self)
            self.more_texts.visibility_changed.connect(lambda visible: self._auxiliary_visibility("texts", visible))
        panel = self.more_texts
        centre = self.mapToGlobal(self._ball_center(FAVORITE_SLOTS).toPoint())
        work = self.screen().availableGeometry()
        edge = self._visual_edge()
        x = centre.x() + 26 if edge == "left" else centre.x() - panel.width() - 26 if edge == "right" else centre.x() - panel.width() // 2
        y = centre.y() + 26 if edge == "top" else centre.y() - panel.height() - 26 if edge == "bottom" else centre.y() - panel.height() // 2
        panel.move(min(max(x, work.left() + 8), work.right() - panel.width() - 7), min(max(y, work.top() + 8), work.bottom() - panel.height() - 7))
        panel.show()
        panel.raise_()
        panel.activateWindow()
        panel.list.setFocus()

    def _action_name(self, index: int) -> str:
        if index < FAVORITE_SLOTS:
            item = self.snippets.favorite(index) if hasattr(self, "snippets") else None
            return self.snippets.display_name(item) if item else f"复制球 {index + 1} · 未配置"
        if index == self._reminder_ball_index() and hasattr(self, "reminders"):
            return f"每日提醒 · {len(self.reminders.unread)} 未读" if self.reminders.unread else "每日提醒 · 暂不可用" if self.reminders.problem else "每日提醒"
        return "更多文本" if index == FAVORITE_SLOTS else "设置" if index == FAVORITE_SLOTS + 2 else "每日提醒"

    def _action_count(self) -> int:
        return FAVORITE_SLOTS + 3

    def set_dock_edge(self, edge: str | None) -> None:
        super().set_dock_edge(edge)
        # Nine full-size actions wrap around the same leaf inside a square
        # stage. The leaf, data positions and collapsed sphere are unchanged.
        self.setFixedSize(WIDTH, 300)
        self._update_mask()

    def _reminder_ball_index(self) -> int:
        return FAVORITE_SLOTS + 1

    def _icon_kind(self, index: int) -> int:
        return index - FAVORITE_SLOTS + 2 if index >= FAVORITE_SLOTS else 0

    def _ball_progress(self, index: int) -> float:
        if self.reduced_motion:
            return self._progress
        elapsed = self._progress * 280
        position = index / (self._action_count() - 1)
        if self._visual_edge() == "left":
            return ease((elapsed - (95 + 60 * position)) / 120)
        return ease((elapsed - (40 + 80 * position)) / 160)

    def _ball_center(self, index: int) -> QPointF:
        amount = self._ball_progress(index)
        edge = self._visual_edge()
        # Copies follow the side contour; the remaining actions continue
        # around the lower edge, keeping 36 DIP hit targets separate.
        side_x = (69, 51, 44, 45, 48, 51, 76, 107, 145)[index]
        side_y = (20, 54, 92, 130, 168, 204, 236, 260, 280)[index]
        if edge == "left":
            return QPointF(WIDTH - side_x - 13 * (1 - amount), side_y)
        if edge in ("top", "bottom"):
            x = (20, 45, 76, 112, 150, 188, 224, 255, 280)[index]
            y = (213, 242, 262, 277, 280, 277, 262, 242, 213)[index]
            return QPointF(x, y - 13 * (1 - amount)) if edge == "top" else QPointF(x, 300 - y + 13 * (1 - amount))
        return QPointF(side_x + 13 * (1 - amount), side_y)

    def _show_ball_tip(self, index: int, label: str) -> None:
        if index < FAVORITE_SLOTS:
            item = self.snippets.favorite(index)
            if item and item.description and label == self._action_name(index):
                label += "\n" + item.description
        QToolTip.showText(self._ball_tip_position(index, label), "<span>" + html.escape(label).replace("\n", "<br>") + "</span>", self)

    def _copy_confirmed(self, index: int) -> bool:
        return index == self._copy_ball and bool(self.copy_feedback)

    def _copied(self, result: CopyResult) -> None:
        self._copy_result = result
        self.copy_feedback = "已复制" if result.succeeded else "复制失败"
        self._feedback_timer.start(2200 if result.succeeded else 3200)
        self.setAccessibleDescription(f"{self.copy_feedback}：{result.name}。{result.message}")
        self.update()

    def _activate_ball(self, index: int) -> None:
        if index < FAVORITE_SLOTS:
            self._copy_ball = index
            item = self.snippets.favorite(index)
            if item:
                self.snippets.copy(item.id, int(self.winId()))
            else:
                self._copied(CopyResult("", f"复制球 {index + 1}", False, "请先在设置中选择常用文本"))
        elif index == FAVORITE_SLOTS:
            self.open_more_texts()
        elif index == FAVORITE_SLOTS + 2:
            self.open_text_settings()
        elif index == self._reminder_ball_index():
            self.open_reminders()
        else:
            super()._activate_ball(index)

    def _paint_icon(self, painter: QPainter, index: int, color: QColor) -> None:
        if self._copy_confirmed(index):
            super()._paint_icon(painter, index, color)
        elif index < FAVORITE_SLOTS:
            item = self.snippets.favorite(index)
            paint_snippet_icon(painter, item.icon_id if item else "copy", color)
        else:
            # The frozen icon painter uses logical more/reminder/settings IDs.
            super()._paint_icon(painter, index, color)

    def _slot_text(self, painter: QPainter, x: float, y: float, text: str, size: float, color: QColor, bold: bool = False) -> None:
        # The contour narrows at the first row; the lower rows keep 156 DIP.
        width = 115 if y < 65 else 156
        fitted = QFontMetricsF(self._font(size, bold)).elidedText(text, Qt.TextElideMode.ElideRight, width)
        self._text(painter, x, y, fitted, size, color, bold)

    def _paint_time_slot(self, painter: QPainter) -> None:
        left = self._visual_edge() == "left"
        title_x, body_x = (145, 105) if left else (95, 95)
        result = self._copy_result
        if self.copy_feedback and result:
            success = result.succeeded
            self._slot_text(painter, title_x, 56, "复制完成" if success else "复制失败", 9.6, self.theme.action if success else self.theme.low, True)
            self._slot_text(painter, body_x, 85, result.name, 13.5, INK, True)
            self._slot_text(painter, 95, 108, "Ctrl+V 粘贴" if success else result.message, 9, MUTED)
            return
        if (index := self._focused_action_index()) is not None:
            hint = "Enter / 空格复制" if index < FAVORITE_SLOTS else "Enter / 空格打开"
            self._slot_text(painter, title_x, 56, f"操作 {index + 1} / {self._action_count()}", 9.2, MUTED, True)
            self._slot_text(painter, body_x, 84, self._action_name(index), 11.8, INK, True)
            self._slot_text(painter, 95, 107, hint, 9, MUTED)
            return
        super()._paint_time_slot(painter)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self._menu.exec(event.globalPos())
        event.accept()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.restore_from_tray()

    def set_explicit_pin(self, value: bool) -> None:
        self._explicit_pin = value
        self.pinned = value
        self._pin_action.setChecked(value)
        if value:
            self.expand()
        else:
            self.clearFocus()
            self._reset_keyboard_focus()
            self._close_timer.start(700)
        self.schedule_save()

    def set_reduced_motion(self, value: bool) -> None:
        self.reduced_motion = value
        self._motion_action.setChecked(value)
        if value:
            self._quota_animation.stop()
            self._previous_sample = None
            self._quota_blend = 1
            self._reminder_animation.stop()
            self._reminder_pulse = 0
        self.update()
        self.schedule_save()

    def _apply_window_behaviour(self, reduced: bool, pinned: bool) -> bool:
        self.set_reduced_motion(reduced)
        self.set_explicit_pin(pinned)
        self._save_timer.stop()
        return self.save_placement()

    def _perform_click(self, x: float, y: float) -> None:
        super()._perform_click(x, y)
        self.pinned = self._explicit_pin

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pressed = self._drag_pending
        super().mouseReleaseEvent(event)
        if pressed and event.button() == Qt.MouseButton.LeftButton:
            # A cancelled action release skips _perform_click. It must still
            # release incidental mouse focus and resume leave reconciliation.
            self._reset_keyboard_focus()
            self.pinned = self._explicit_pin
            self.clearFocus()
            self._pulse.start(32)
            self._check_cursor_and_animate()

    def collapse(self) -> None:
        if self._explicit_pin or self._menu_open or self._auxiliary_open:
            return
        super().collapse()

    def enterEvent(self, event: QEnterEvent) -> None:
        self._pulse.start(32)
        self._check_cursor_and_animate()
        super().enterEvent(event)

    def expand(self) -> None:
        self._pulse.start(32)
        super().expand()

    def _visible_hit(self, x: float, y: float) -> bool:
        if (self.dock_edge is not None and self._progress <= .001
                and self._expansion.state() == QAbstractAnimation.State.Stopped):
            centre = self._dock_center()
            return (x - centre.x()) ** 2 + (y - centre.y()) ** 2 <= DOCK_RADIUS ** 2
        return super()._visible_hit(x, y)

    def _check_cursor_and_animate(self) -> None:
        if not self._menu_open and not self._auxiliary_open:
            if (self.dock_edge is not None and self._progress <= .001 and not self._drag_pending
                    and self._expansion.state() == QAbstractAnimation.State.Stopped):
                local = self.mapFromGlobal(QCursor.pos())
                if not self._visible_hit(local.x(), local.y()):
                    if self._pulse.interval() != 64:
                        self._pulse.start(64)
                    self._open_timer.stop()
                    self._close_timer.stop()  # Already fully collapsed.
                    if self._last_inside:
                        self._hover_timer.stop()
                        self._detail_timer.stop()
                        self._last_inside = False
                    if self.testAttribute(Qt.WidgetAttribute.WA_SetCursor):
                        self.unsetCursor()
                    return  # No repeated cursor mutation or painted-shell work.
            if self._pulse.interval() != 32:
                self._pulse.start(32)
            super()._check_cursor_and_animate()
            if (self.dock_edge is not None and not self._drag_pending and not self.pinned
                    and not self._explicit_pin and not self.hasFocus()):
                if self._last_inside:
                    self._close_timer.stop()
                elif (self._progress > .001 and not self._close_timer.isActive()
                      and self._expansion.state() == QAbstractAnimation.State.Stopped):
                    # A close attempted during a lock/focus transition can be
                    # rejected. Re-arm once after release, never on every tick.
                    self._close_timer.start(700)
            # Region changes/inactive tool windows do not reliably deliver a
            # new Qt Enter event. Keep the original 32 ms check alive; the
            # collapsed hit above avoids constructing a painted shell path.

    def hide_to_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._show_ball_tip(FAVORITE_SLOTS + 2, "托盘不可用，浮窗保持可见")
            return
        self.save_placement()
        self.hide()
        self._pulse.stop()
        self.runtime.set_expanded(False)

    def restore_from_tray(self) -> None:
        self.restore_current()
        self.show()
        self.raise_()
        self._pulse.start(32)
        if self._explicit_pin or self.dock_edge is None:
            self.expand()

    def reset_placement(self) -> None:
        self.apply_placement(None)
        self.show()
        self._pulse.start(32)
        self.save_placement()

    def _screen_added(self, screen: QScreen, schedule: bool = True) -> None:
        screen.geometryChanged.connect(lambda rect: self._screen_timer.start(120))
        screen.availableGeometryChanged.connect(lambda rect: self._screen_timer.start(120))
        screen.logicalDotsPerInchChanged.connect(lambda dpi: self._screen_timer.start(120))
        if schedule:
            self._screen_timer.start(120)

    def restore_current(self) -> None:
        if self._drag_pending:
            self._drag_pending = False
            self._drag_started = False
            self.releaseMouse()
        self.apply_placement(self._saved)

    def apply_placement(self, placement: Placement | None) -> None:
        screens = QApplication.screens()
        screen = next((item for item in screens if placement and screen_key(item) == placement.monitor_key), QApplication.primaryScreen())
        monitor = screen_monitor(screen)
        place = placement or Placement(monitor.key, "right")
        if place.monitor_key != monitor.key:
            place = replace(place, monitor_key=monitor.key)
        self._restoring = True
        self._free_edge = place.free_orientation
        self.set_dock_edge(place.edge)
        x, y = place.position(monitor, self.width(), self.height())
        if place.edge and not exterior_edge(monitor, place.edge, y + self.height() / 2 if place.edge in ("left", "right") else x + self.width() / 2,
                                             tuple(screen_monitor(item) for item in screens)):
            # A saved outer edge can become a seam after another screen appears.
            self.set_dock_edge(None)
            place = replace(place, edge=None)
            x, y = place.position(monitor, self.width(), self.height())
        self.move(round(x), round(y))
        self._explicit_pin = place.pinned
        self.pinned = place.pinned
        self.set_expansion_progress(1 if place.pinned or place.edge is None else 0)
        self.runtime.set_expanded(place.pinned or place.edge is None)
        self._saved = place
        if hasattr(self, "_pin_action"):
            self._pin_action.blockSignals(True)
            self._pin_action.setChecked(place.pinned)
            self._pin_action.blockSignals(False)
        self._restoring = False
        self._update_mask()

    def _finish_drag(self, pointer: QPoint) -> None:
        screen = QApplication.screenAt(pointer) or self.screen() or QApplication.primaryScreen()
        monitor = screen_monitor(screen)
        monitors = tuple(screen_monitor(item) for item in QApplication.screens())
        delta = pointer - self._drag_origin_global
        edge = nearest_dock(monitor, monitors, self.x(), self.y(), WIDTH, self.height(), delta.x(), delta.y())
        self.set_dock_edge(edge)
        x, y = monitor.work.clamp(self.x(), self.y(), self.width(), self.height())
        if edge == "left":
            x = monitor.work.x
        elif edge == "right":
            x = max(monitor.work.x, monitor.work.right - self.width())
        elif edge == "top":
            y = monitor.work.y
        elif edge == "bottom":
            y = max(monitor.work.y, monitor.work.bottom - self.height())
        self.move(round(x), round(y))
        self.pinned = self._explicit_pin
        if edge is None or self._explicit_pin:
            self.expand()
        self._update_mask()
        self.update()
        local = self.mapFromGlobal(pointer)
        self._last_inside = self._visible_hit(local.x(), local.y())
        if edge and not self._last_inside:
            self._close_timer.start(700)
        self.save_placement()

    def schedule_save(self) -> None:
        if self._ready_desktop and not self._restoring and not self._drag_pending:
            self._save_timer.start(250)

    def moveEvent(self, event: QMoveEvent) -> None:
        super().moveEvent(event)
        self.schedule_save()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.schedule_save()

    def save_placement(self) -> bool:
        screen = self.screen() or QApplication.primaryScreen()
        place = capture_placement(screen_monitor(screen), self.x(), self.y(), self.width(), self.height(),
                                  cast(Edge | None, self.dock_edge), self._explicit_pin, cast(Edge, self._free_edge))
        self._saved = place
        try:
            self._settings.save(DesktopSettings(place, self.reduced_motion))
        except StorageError as error:
            self._storage_problem(str(error))
            return False
        return True

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_P and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.set_explicit_pin(not self._explicit_pin)
        elif event.key() == Qt.Key.Key_M:
            self.set_reduced_motion(not self.reduced_motion)
        elif event.key() == Qt.Key.Key_Q and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.quit_app()
        else:
            super().keyPressEvent(event)
            if self._explicit_pin:
                self.pinned = True

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._quitting:
            self.save_placement()
            event.accept()
        else:
            self.hide_to_tray()
            event.ignore()

    def quit_app(self) -> None:
        self._quitting = True
        self._save_timer.stop()
        self._screen_timer.stop()
        self.save_placement()
        self.tray.hide()
        self.snippets.stop()
        self.reminders.stop()
        for panel in (self.text_settings, self.more_texts):
            if panel:
                panel.hide()
        self.runtime.stop()
        QApplication.quit()

    def nativeEvent(self, event_type: object, message: int) -> tuple[bool, int]:
        if os.name == "nt":
            native = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
            if native.message == 0x0218 and native.wParam in (0x0007, 0x0012):  # WM_POWERBROADCAST resume events
                QTimer.singleShot(0, self.resumed.emit)
        return False, 0
