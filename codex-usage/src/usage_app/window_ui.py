"""Window behaviour settings use explicit persistence and optional startup."""
from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton, QVBoxLayout, QWidget

from .autostart import Autostart
from .messages import product_message
from .storage import StorageError


class WindowPage(QWidget):
    def __init__(self, *, reduced_motion: bool, pinned: bool, startup: Autostart,
                 apply: Callable[[bool, bool], bool], reset: Callable[[], None], snapshot: Callable[[], tuple[bool, bool]] | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.startup = startup
        self.apply = apply
        self.snapshot = snapshot
        self._dirty = False
        self._loading = False
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 12, 0, 0)
        root.setSpacing(16)
        self.reduced = QCheckBox("减少动态效果")
        self.reduced.setChecked(reduced_motion)
        self.pinned = QCheckBox("固定展开")
        self.pinned.setChecked(pinned)
        self.launch = QCheckBox("登录 Windows 后启动usage")
        startup_error: StorageError | None = None
        try:
            self.launch.setChecked(startup.enabled())
        except StorageError as error:
            startup_error = error
            self.launch.setEnabled(False)
        root.addWidget(self.reduced)
        note = QLabel("取消后，悬浮展开、移出收起；拖到屏幕内部时保持展开。")
        note.setObjectName("muted")
        note.setWordWrap(True)
        root.addWidget(self.pinned)
        root.addWidget(note)
        root.addWidget(self.launch)
        boundary = QLabel("开机启动为可选项，保存后才修改本用户的启动设置；应用不唤醒电脑，退出或睡眠期间不保证提醒。")
        boundary.setObjectName("muted")
        boundary.setWordWrap(True)
        root.addWidget(boundary)
        self.save_button = QPushButton("保存窗口行为")
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(self.save)
        root.addWidget(self.save_button)
        self.status = QLabel(str(startup_error) if startup_error else "拖动位置会自动保存，重启后恢复到可见工作区。")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        reset_button = QPushButton("回到主屏右侧")
        reset_button.clicked.connect(reset)
        root.addWidget(reset_button)
        instruction = QLabel("Ctrl+P 固定展开，M 切换减少动态效果，R 刷新额度；右键或托盘可找回、隐藏和退出。")
        instruction.setObjectName("muted")
        instruction.setWordWrap(True)
        root.addWidget(instruction)
        root.addStretch()
        for checkbox in (self.reduced, self.pinned, self.launch):
            checkbox.toggled.connect(self._mark_dirty)

    def _mark_dirty(self) -> None:
        if not self._loading:
            self._dirty = True

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self._dirty:
            return
        self._loading = True
        try:
            if self.snapshot:
                reduced, pinned = self.snapshot()
                self.reduced.setChecked(reduced)
                self.pinned.setChecked(pinned)
            self.launch.setChecked(self.startup.enabled())
            self.launch.setEnabled(True)
        except StorageError as error:
            self.status.setText(product_message(error))
            self.launch.setEnabled(False)
        finally:
            self._loading = False

    def save(self) -> None:
        if not self.apply(self.reduced.isChecked(), self.pinned.isChecked()):
            self.status.setText("显示已调整，但设置未能保存；重启仍使用上次保存值。")
            return
        try:
            if self.launch.isEnabled():
                self.startup.set_enabled(self.launch.isChecked())
            self._dirty = False
            self.status.setText("窗口行为已保存。" if self.launch.isEnabled() else "显示设置已保存；开机启动暂不可用。")
        except StorageError as error:
            self.status.setText("显示设置已保存；" + product_message(error))
