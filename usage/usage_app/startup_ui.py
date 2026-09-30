"""Visible startup failures, including when launched without a console."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

from .messages import product_message
from .text_ui import STYLE


def startup_error(error: Exception, data_dir: Path | None) -> QMessageBox:
    message = QMessageBox()
    message.setWindowTitle("usage · 无法启动")
    message.setStyleSheet(STYLE)
    message.setIcon(QMessageBox.Icon.Warning)
    message.setTextFormat(Qt.TextFormat.PlainText)
    message.setText(product_message(error))
    message.setInformativeText("现有配置与文本已保留。请检查数据文件，或使用 README 中的备份恢复步骤。")
    if data_dir is not None and data_dir.is_dir():
        folder = message.addButton("打开数据目录", QMessageBox.ButtonRole.ActionRole)
        folder.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir))))
    exit_button = message.addButton("退出", QMessageBox.ButtonRole.RejectRole)
    message.setDefaultButton(exit_button)
    return message
