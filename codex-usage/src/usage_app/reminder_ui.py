"""Daily reminder settings and an unread list in the existing sectioned form."""
from __future__ import annotations

import html
from datetime import time

from PySide6.QtCore import QSize, Qt, QTime
from PySide6.QtGui import QFont, QFontMetricsF
from PySide6.QtWidgets import QCheckBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QTimeEdit, QVBoxLayout, QWidget

from .icons import icon_for
from .reminder_service import ReminderService
from .storage import StorageError


class ReminderPage(QWidget):
    def __init__(self, service: ReminderService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.current_id: str | None = None
        self._draft = False
        self._baseline: tuple[str, time, bool] | None = None
        self._delete_confirm: str | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        root.setSpacing(12)
        body = QHBoxLayout()
        body.setSpacing(20)
        left = QVBoxLayout()
        self.list = QListWidget()
        self.list.setMinimumWidth(205)
        self.list.setMaximumWidth(250)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setIconSize(QSize(22, 22))
        self.list.setAccessibleName("每日提醒列表")
        self.list.currentItemChanged.connect(self._selected)
        left.addWidget(self.list, 1)
        self.add_button = QPushButton("新增提醒")
        self.add_button.clicked.connect(self.new_item)
        left.addWidget(self.add_button)
        body.addLayout(left, 2)
        right = QVBoxLayout()
        right.setSpacing(10)
        self.title = QLineEdit()
        self.title.setMaxLength(80)
        self.title.setPlaceholderText("例如：收尾复盘")
        self.time = QTimeEdit(QTime(18, 0))
        self.time.setDisplayFormat("HH:mm")
        self.time.setKeyboardTracking(False)
        self.time.setAccessibleName("每日本地时间")
        self.enabled = QCheckBox("启用每日提醒")
        self.enabled.setChecked(True)
        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.addRow("事项", self.title)
        form.addRow("每天", self.time)
        form.addRow("", self.enabled)
        right.addLayout(form)
        self.zone = QLabel()
        self.zone.setObjectName("muted")
        self.zone.setWordWrap(True)
        right.addWidget(self.zone)
        self.save_button = QPushButton("保存每日提醒")
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(self.save_item)
        right.addWidget(self.save_button)
        self.status = QLabel()
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        right.addWidget(self.status)
        label = QLabel("未读事项")
        label.setStyleSheet("font-weight: 600; padding-top: 8px;")
        right.addWidget(label)
        self.unread = QListWidget()
        self.unread.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.unread.setMinimumHeight(100)
        self.unread.setAccessibleName("仍未确认的提醒事项")
        right.addWidget(self.unread, 1)
        self.no_unread = QLabel("没有未读提醒。")
        self.no_unread.setObjectName("muted")
        right.addWidget(self.no_unread)
        row = QHBoxLayout()
        self.ack_button = QPushButton("全部标为已读")
        self.ack_button.clicked.connect(service.acknowledge_all)
        self.delete_button = QPushButton("删除提醒")
        self.delete_button.clicked.connect(self.delete_item)
        row.addWidget(self.ack_button)
        row.addStretch()
        row.addWidget(self.delete_button)
        right.addLayout(row)
        body.addLayout(right, 3)
        root.addLayout(body, 1)
        note = QLabel("应用运行、电脑唤醒时生效。只补发当天未提醒的事项；Windows 勿扰可能阻止通知展示，未读仍会留在铃铛中。")
        note.setObjectName("muted")
        note.setWordWrap(True)
        root.addWidget(note)
        service.changed.connect(self.reload_items)
        service.error.connect(self.status.setText)
        self.reload_items()

    def _form_values(self) -> tuple[str, time, bool]:
        clock = self.time.time()
        return self.title.text(), time(clock.hour(), clock.minute()), self.enabled.isChecked()

    def reload_items(self) -> None:
        self.list.blockSignals(True)
        old_scroll = self.list.verticalScrollBar().value()
        self.list.clear()
        selected = None
        font = QFont("Microsoft YaHei UI")
        font.setPointSizeF(9.5)
        metrics = QFontMetricsF(font)
        for item in self.service.items:
            title = metrics.elidedText(item.title, Qt.TextElideMode.ElideRight, 195)
            row = QListWidgetItem(icon_for("note"), title + f"\n{item.local_time:%H:%M} · {'每天' if item.enabled else '已停用'}")
            row.setData(Qt.ItemDataRole.UserRole, item.id)
            row.setToolTip(html.escape(item.title))
            self.list.addItem(row)
            if item.id == self.current_id:
                selected = row
        if self._draft:
            self.list.clearSelection()
        elif selected:
            self.list.setCurrentItem(selected)
            if self._form_values() == self._baseline:
                self._selected(selected, None)
        elif self.service.items:
            self.list.setCurrentRow(0)
            self._selected(self.list.currentItem(), None)
        else:
            self.new_item()
        self.list.verticalScrollBar().setValue(old_scroll)
        self.list.blockSignals(False)
        self.unread.clear()
        for occurrence in self.service.unread:
            row = QListWidgetItem(occurrence.title + f"\n{occurrence.scheduled_at.astimezone():%m/%d %H:%M} · 未确认")
            row.setToolTip(html.escape(occurrence.title))
            self.unread.addItem(row)
        has_unread = bool(self.service.unread)
        self.unread.setVisible(has_unread)
        self.no_unread.setVisible(not has_unread)
        self.ack_button.setEnabled(has_unread)
        try:
            self.zone.setText("本机时区 · " + self.service.clock.read().zone_label)
        except StorageError as error:
            self.zone.setText(str(error))
        if self.service.problem:
            self.status.setText(self.service.problem)

    def _selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        item = next((value for value in self.service.items if value.id == current.data(Qt.ItemDataRole.UserRole)), None)
        if item:
            self._draft = False
            self.current_id = item.id
            self.title.setText(item.title)
            self.time.setTime(QTime(item.local_time.hour, item.local_time.minute))
            self.enabled.setChecked(item.enabled)
            self._baseline = self._form_values()
            self._delete_confirm = None
            self.delete_button.setText("删除提醒")
            self.delete_button.setEnabled(True)
            self.status.setText("每天一次；同一天改时间或重新启用不会重复已经提醒过的事项。")

    def new_item(self) -> None:
        self._draft = True
        self.current_id, self._baseline = None, None
        self.list.clearSelection()
        self.title.clear()
        self.enabled.setChecked(True)
        self.delete_button.setEnabled(False)
        self.status.setText("填写事项与时间。今天已过的时间会从明天开始。")

    def save_item(self) -> None:
        title, local_time, enabled = self._form_values()
        try:
            if self.current_id:
                item = self.service.store.update(self.current_id, title, local_time, enabled)
            else:
                item = self.service.store.add(title, local_time, self.service.clock.read().now, enabled=enabled)
            self.current_id, self._draft, self._baseline = item.id, False, self._form_values()
            self.service.reload()
            self.status.setText("每日提醒已保存。" if enabled else "提醒已停用。")
            self.service.poll()
        except (StorageError, ValueError) as error:
            self.status.setText(str(error))

    def delete_item(self) -> None:
        if self.current_id is None:
            return
        if self._delete_confirm != self.current_id:
            self._delete_confirm = self.current_id
            self.delete_button.setText("确认删除")
            self.status.setText("再次点击确认：移除每日提醒，并将这项未读标为已读。")
            return
        try:
            self.service.delete(self.current_id)
            self.current_id, self._draft = None, False
            self.service.reload()
        except StorageError as error:
            self.status.setText(str(error))
