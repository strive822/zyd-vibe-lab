"""Window behaviour settings use explicit persistence and optional startup."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QThreadPool, Qt, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton, QVBoxLayout, QWidget

from .autostart import Autostart
from .startup_job import StartupJob


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
        self._startup_job: StartupJob | None = None
        self._saving_startup = False
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 12, 0, 0)
        root.setSpacing(16)
        self.reduced = QCheckBox("减少动态效果")
        self.reduced.setChecked(reduced_motion)
        self.pinned = QCheckBox("固定展开")
        self.pinned.setChecked(pinned)
        self.launch = QCheckBox("登录 Windows 后启动usage")
        # Construction of an unselected page must not query the desktop.
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
        self.status = QLabel("拖动位置会自动保存，重启后恢复到可见工作区。")
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
        if self._dirty or self._startup_job is not None:
            return
        self._loading = True
        try:
            if self.snapshot:
                reduced, pinned = self.snapshot()
                self.reduced.setChecked(reduced)
                self.pinned.setChecked(pinned)
        finally:
            self._loading = False
        self._start_startup_job(None)

    def _start_startup_job(self, enabled: bool | None) -> None:
        self._saving_startup = enabled is not None
        self.launch.setEnabled(False)
        self.save_button.setEnabled(False)
        if self._saving_startup:
            self.reduced.setEnabled(False)
            self.pinned.setEnabled(False)
        self.status.setText("正在保存开机启动设置…" if self._saving_startup else "正在读取开机启动设置…")
        job = StartupJob(self.startup, enabled)
        self._startup_job = job
        job.result.finished.connect(self._startup_finished, Qt.ConnectionType.QueuedConnection)
        QThreadPool.globalInstance().start(job)

    @Slot(bool, str)
    def _startup_finished(self, enabled: bool, error: str) -> None:
        saving = self._saving_startup
        self._startup_job = None
        self._saving_startup = False
        self.reduced.setEnabled(True)
        self.pinned.setEnabled(True)
        self.save_button.setEnabled(True)
        self.launch.setEnabled(saving or not error)
        if error:
            self.status.setText(("显示设置已保存；" if saving else "") + error)
            return
        if saving:
            self._dirty = False
            self.status.setText("窗口行为已保存。")
        else:
            self._loading = True
            self.launch.setChecked(enabled)
            self._loading = False
            self.status.setText("拖动位置会自动保存，重启后恢复到可见工作区。")

    def save(self) -> None:
        if self._startup_job is not None:
            return
        if not self.apply(self.reduced.isChecked(), self.pinned.isChecked()):
            self.status.setText("显示已调整，但设置未能保存；重启仍使用上次保存值。")
            return
        if self.launch.isEnabled():
            self._start_startup_job(self.launch.isChecked())
        else:
            self._dirty = False
            self.status.setText("显示设置已保存；开机启动暂不可用。")
