"""The first settings section and compact named-text panel, in the frozen palette."""
from __future__ import annotations

import html
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QFont, QFontMetricsF, QHideEvent, QKeyEvent, QShowEvent
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from .icons import icon_for
from .snippet_service import CopyResult, SnippetService
from .snippets import ICON_IDS, Snippet
from .storage import StorageError
from .messages import product_message

STYLE = """
QDialog { background: #f5f2e9; color: #1e2119; }
QWidget#sectionPage { background: #f5f2e9; }
QScrollArea { background: transparent; border: none; }
QWidget { font: 9.5pt 'Microsoft YaHei UI'; color: #1e2119; }
QLabel#eyebrow { color: #58623d; font: 9pt 'Microsoft YaHei UI'; }
QLabel#heading { font: 17pt 'Microsoft YaHei UI'; font-weight: 600; }
QLabel#muted { color: #686c63; font: 9pt 'Microsoft YaHei UI'; }
QLabel#status { color: #686c63; font: 9pt 'Microsoft YaHei UI'; padding-top: 4px; }
QLineEdit, QComboBox, QPlainTextEdit, QAbstractSpinBox { background: #faf8f2; border: 1px solid #b9bdad; padding: 6px; selection-background-color: #58623d; selection-color: #f5f2e9; }
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QAbstractSpinBox:focus { border: 2px solid #58623d; padding: 5px; }
QAbstractSpinBox::up-button, QAbstractSpinBox::down-button { background: #f5f2e9; border-left: 1px solid #b9bdad; width: 24px; }
QCheckBox { spacing: 8px; padding: 4px 0; border-bottom: 1px solid transparent; }
QCheckBox::indicator { background: #faf8f2; border: 1px solid #9fa48f; width: 16px; height: 16px; }
QCheckBox:focus { border-bottom: 1px solid #58623d; }
QComboBox::drop-down { width: 24px; border: none; }
QPushButton { background: #f5f2e9; border: 1px solid #9fa48f; padding: 7px 10px; }
QPushButton:hover { background: #e9eadc; }
QPushButton:focus { border: 2px solid #58623d; padding: 6px 9px; }
QPushButton:pressed { background: #dfe3cf; }
QPushButton:disabled { color: #92958b; border-color: #d0d1c6; }
QPushButton#primary { color: #f5f2e9; background: #58623d; border-color: #58623d; }
QPushButton#primary:hover { background: #46522f; }
QPushButton#section { border: none; border-bottom: 2px solid transparent; padding: 8px 10px; background: transparent; }
QPushButton#section[navSelected="true"] { border-bottom-color: #58623d; color: #58623d; font-weight: 600; }
QPushButton#section:focus { border: 1px solid #58623d; padding: 7px 9px; }
QListWidget { background: transparent; border: none; border-right: 1px solid #c9c9b9; outline: 0; }
QListWidget::item { padding: 10px 8px; border-bottom: 1px solid #deded0; }
QListWidget::item:selected { background: #dfe3cf; color: #1e2119; }
QListWidget::item:focus { border-left: 2px solid #58623d; }
QScrollBar:vertical { background: #eeeede; width: 9px; margin: 0; }
QScrollBar::handle:vertical { background: #9fa48f; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""
STYLE += 'QComboBox::down-arrow { image: url("' + (Path(__file__).parent / "assets" / "chevron.svg").as_posix() + '"); width: 12px; height: 8px; }'
for _selector, _asset in (("QAbstractSpinBox::up-arrow", "chevron-up.svg"), ("QAbstractSpinBox::down-arrow", "chevron.svg"), ("QCheckBox::indicator:checked", "check.svg")):
    STYLE += _selector + ' { image: url("' + (Path(__file__).parent / "assets" / _asset).as_posix() + '"); }'


def item_label(service: SnippetService, item: Snippet) -> str:
    name = service.display_name(item)
    description = item.description or "无说明"
    if item.favorite_slot is not None:
        description = f"复制球 {item.favorite_slot + 1} · {description}"
    font = QFont("Microsoft YaHei UI", 9)
    return QFontMetricsF(font).elidedText(name, Qt.TextElideMode.ElideRight, 195) + "\n" + QFontMetricsF(font).elidedText(description, Qt.TextElideMode.ElideRight, 195)


class AuxiliaryDialog(QDialog):
    visibility_changed = Signal(bool)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # A list's Enter activation must not also press an unrelated default
            # dialog button after the list emits itemActivated.
            focused = self.focusWidget()
            if isinstance(focused, QPushButton):
                focused.click()
            event.accept()
            return
        super().keyPressEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.visibility_changed.emit(True)

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        self.visibility_changed.emit(False)


class SnippetSettings(AuxiliaryDialog):
    def __init__(self, service: SnippetService) -> None:
        # Independent normal window: an owned window can inherit its topmost
        # leaf's Z-order on Windows even after removing the Qt topmost flag.
        flags = (Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowSystemMenuHint
                 | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint
                 | Qt.WindowType.WindowCloseButtonHint)
        super().__init__(None, flags)
        self.service = service
        self.current_id: str | None = None
        self._draft = False
        self._baseline: tuple[str, str, str, int | None] | None = None
        self._delete_confirm: str | None = None
        self.setWindowTitle("usage · 快捷文本")
        self.setStyleSheet(STYLE)
        self.resize(720, 650)
        self.setMinimumSize(560, 480)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(12)
        self.eyebrow = eyebrow = QLabel("usage / 快捷文本")
        eyebrow.setObjectName("eyebrow")
        self.heading = heading = QLabel("把常用文字放在手边")
        heading.setObjectName("heading")
        self.lead = lead = QLabel("先保存名字与说明，再用系统记事本编辑正文。")
        lead.setObjectName("muted")
        lead.setWordWrap(True)
        root.addWidget(eyebrow)
        root.addWidget(heading)
        root.addWidget(lead)
        self.navigation = QHBoxLayout()
        self.navigation.setSpacing(8)
        root.addLayout(self.navigation)
        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)
        self._sections: dict[str, tuple[str, str, str, QWidget, QPushButton]] = {}
        text_page = QWidget()
        editor_root = QVBoxLayout(text_page)
        editor_root.setContentsMargins(0, 8, 0, 0)
        editor_root.setSpacing(12)
        body = QHBoxLayout()
        body.setSpacing(20)
        left = QVBoxLayout()
        self.list = QListWidget()
        self.list.setMinimumWidth(205)
        self.list.setMaximumWidth(250)
        self.list.setIconSize(QSize(22, 22))
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setAccessibleName("已保存的快捷文本")
        self.list.currentItemChanged.connect(self._selected)
        left.addWidget(self.list, 1)
        self.add_button = QPushButton("新增文本")
        self.add_button.clicked.connect(self.new_item)
        left.addWidget(self.add_button)
        body.addLayout(left, 2)
        right = QVBoxLayout()
        right.setSpacing(10)
        self.name = QLineEdit()
        self.name.setMaxLength(80)
        self.name.setPlaceholderText("例如：代码评审")
        self.description = QLineEdit()
        self.description.setMaxLength(240)
        self.description.setPlaceholderText("这条文本用于什么场景")
        self.icons = QComboBox()
        for identity, label in zip(ICON_IDS, ("复制", "文字", "代码", "检查", "笔记")):
            self.icons.addItem(icon_for(identity), label, identity)
        self.favorite = QComboBox()
        for label, value in (("不放在常用球", None), ("第一个复制球", 0), ("第二个复制球", 1), ("第三个复制球", 2), ("第四个复制球", 3), ("第五个复制球", 4), ("第六个复制球", 5)):
            self.favorite.addItem(label, value)
        form = QFormLayout()
        form.setVerticalSpacing(10)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.addRow("名字", self.name)
        form.addRow("说明", self.description)
        form.addRow("图标", self.icons)
        form.addRow("常用位", self.favorite)
        right.addLayout(form)
        self.save_button = QPushButton("保存名字与设置")
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(self.save_item)
        right.addWidget(self.save_button)
        row = QHBoxLayout()
        self.edit_button = QPushButton("用记事本编辑")
        self.edit_button.clicked.connect(self.open_notepad)
        self.reload_button = QPushButton("重新读取正文")
        self.reload_button.setToolTip("读取记事本已经保存的正文；自动更新未生效时可手动刷新。")
        self.reload_button.setAccessibleDescription("读取文件中已经保存的正文，不会保存记事本里尚未保存的修改。")
        self.reload_button.clicked.connect(self.refresh_preview)
        row.addWidget(self.edit_button)
        row.addWidget(self.reload_button)
        right.addLayout(row)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("保存的正文将出现在这里")
        self.preview.setAccessibleName("记事本已保存正文预览")
        self.preview.setMinimumHeight(90)
        right.addWidget(self.preview, 1)
        self.status = QLabel("还没有快捷文本，先新增一条。")
        self.status.setObjectName("status")
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        right.addWidget(self.status)
        buttons = QHBoxLayout()
        self.up_button, self.down_button = QPushButton("上移"), QPushButton("下移")
        self.up_button.clicked.connect(lambda: self.move_item(-1))
        self.down_button.clicked.connect(lambda: self.move_item(1))
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self.delete_item)
        buttons.addWidget(self.up_button)
        buttons.addWidget(self.down_button)
        buttons.addStretch()
        buttons.addWidget(self.delete_button)
        right.addLayout(buttons)
        body.addLayout(right, 3)
        editor_root.addLayout(body, 1)
        note = QLabel("在记事本中按 Ctrl+S；预览没更新时点“重新读取正文”。未保存的改动不参与复制。")
        note.setObjectName("muted")
        note.setWordWrap(True)
        editor_root.addWidget(note)
        self.add_section("texts", "快捷文本", "把常用文字放在手边", "先保存名字与说明，再用系统记事本编辑正文。", text_page)
        self.select_section("texts")
        service.changed.connect(self.reload_items)
        service.content_changed.connect(self._content_changed)
        service.error.connect(self.status.setText)
        self.reload_items()

    def add_section(self, identity: str, label: str, heading: str, lead: str, page: QWidget) -> None:
        page.setObjectName("sectionPage")
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(page)
        button = QPushButton(label)
        button.setObjectName("section")
        button.clicked.connect(lambda: self.select_section(identity))
        self.navigation.addWidget(button)
        self.pages.addWidget(scroll)
        self._sections[identity] = label, heading, lead, scroll, button

    def select_section(self, identity: str) -> None:
        label, heading, lead, page, button = self._sections[identity]
        self.pages.setCurrentWidget(page)
        self.setWindowTitle("usage · " + label)
        self.eyebrow.setText("usage / " + label)
        self.heading.setText(heading)
        self.lead.setText(lead)
        for item in self._sections.values():
            item[4].setProperty("navSelected", item[4] is button)
            item[4].style().unpolish(item[4])
            item[4].style().polish(item[4])

    def reload_items(self) -> None:
        current = self.current_id
        self.list.blockSignals(True)
        self.list.clear()
        selected = None
        for item in self.service.items:
            row = QListWidgetItem(icon_for(item.icon_id), item_label(self.service, item))
            row.setData(Qt.ItemDataRole.UserRole, item.id)
            row.setToolTip("<span>" + html.escape(item.name + "\n" + item.description).replace("\n", "<br>") + "</span>")
            self.list.addItem(row)
            if item.id == current:
                selected = row
        if self._draft:
            self.list.clearSelection()
        elif selected:
            self.list.setCurrentItem(selected)
            if self._baseline == self._form_values():
                self._selected(selected, None)
        elif self.service.items:
            self.list.setCurrentRow(0)
            self._selected(self.list.currentItem(), None)
        else:
            self.new_item()
        self.list.blockSignals(False)
        if self.service.problem:
            self.status.setText(self.service.problem)

    def _form_values(self) -> tuple[str, str, str, int | None]:
        return self.name.text(), self.description.text(), str(self.icons.currentData()), self.favorite.currentData()

    def _selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        identity = current.data(Qt.ItemDataRole.UserRole)
        item = next((item for item in self.service.items if item.id == identity), None)
        if item:
            self._draft = False
            self.current_id = item.id
            self.name.setText(item.name)
            self.description.setText(item.description)
            self.icons.setCurrentIndex(ICON_IDS.index(item.icon_id))
            self.favorite.setCurrentIndex(0 if item.favorite_slot is None else item.favorite_slot + 1)
            self._baseline = self._form_values()
            self._delete_confirm = None
            self.delete_button.setText("删除")
            self._set_existing(True)
            self.refresh_preview()

    def _set_existing(self, value: bool) -> None:
        for button in (self.edit_button, self.reload_button, self.delete_button, self.up_button, self.down_button):
            button.setEnabled(value)

    def new_item(self) -> None:
        self._draft = True
        self.current_id = None
        self._baseline = None
        self.list.clearSelection()
        self.name.clear()
        self.description.clear()
        self.icons.setCurrentIndex(0)
        self.favorite.setCurrentIndex(0)
        self.preview.clear()
        self._set_existing(False)
        self.status.setText("填写名字并保存，即可用记事本编辑。")
        self.name.setFocus()

    def save_item(self) -> None:
        try:
            if self.current_id is None:
                item = self.service.store.add(self.name.text(), self.description.text(), str(self.icons.currentData()), self.favorite.currentData())
            else:
                item = self.service.store.update(self.current_id, name=self.name.text(), description=self.description.text(),
                                                icon_id=str(self.icons.currentData()), favorite_slot=self.favorite.currentData())
            self.current_id = item.id
            self._draft = False
            self._baseline = self._form_values()
            self.service.reload()
            self.status.setText("名字与设置已保存；正文请用记事本编辑。")
        except (ValueError, StorageError) as error:
            self.status.setText(product_message(error))

    def refresh_preview(self) -> None:
        if self.current_id:
            content = self.service.read(self.current_id)
            self.preview.setPlainText(content.text[:4000] if content.text is not None else "")
            self.status.setText(content.message + f" · {content.loaded_at.astimezone():%H:%M:%S}")

    def _content_changed(self, identity: str) -> None:
        if identity == self.current_id:
            self.refresh_preview()

    def open_notepad(self) -> None:
        if self.current_id:
            try:
                self.service.edit_in_notepad(self.current_id)
                self.hide()  # Give the external editor space and release the leaf's interaction lock.
            except StorageError as error:
                self.status.setText(product_message(error))

    def move_item(self, direction: int) -> None:
        identities = [item.id for item in self.service.items]
        if self.current_id in identities:
            index = identities.index(self.current_id)
            target = index + direction
            if 0 <= target < len(identities):
                identities[index], identities[target] = identities[target], identities[index]
                try:
                    self.service.store.reorder(tuple(identities))
                    self.service.reload()
                except StorageError as error:
                    self.status.setText(product_message(error))

    def delete_item(self) -> None:
        if self.current_id is None:
            return
        if self._delete_confirm != self.current_id:
            self._delete_confirm = self.current_id
            self.delete_button.setText("确认删除")
            self.status.setText("再次点击确认：会删除这条快捷文本及其正文。")
            return
        try:
            self.service.store.delete(self.current_id)
            self.current_id = None
            self._draft = False
            self.service.reload()
        except StorageError as error:
            self.status.setText(product_message(error))


class MoreTexts(AuxiliaryDialog):
    def __init__(self, service: SnippetService, manage: Callable[[], None], parent: QWidget) -> None:
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.service = service
        self.manage = manage
        self.setWindowTitle("usage · 更多文本")
        self.setStyleSheet(STYLE)
        self.resize(320, 360)
        self.setMinimumSize(260, 240)
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        heading = QLabel("按名字复制")
        heading.setObjectName("heading")
        root.addWidget(heading)
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setIconSize(QSize(22, 22))
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.list.itemClicked.connect(self.copy_item)
        self.list.itemActivated.connect(self.copy_item)
        root.addWidget(self.list, 1)
        self.status = QLabel("点击或按 Enter 复制，不会自动粘贴。")
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        button = QPushButton("管理快捷文本")
        button.clicked.connect(self.open_manage)
        root.addWidget(button)
        service.changed.connect(self.reload_items)
        self.reload_items()

    def reload_items(self) -> None:
        current = self.list.currentItem()
        current_id = current.data(Qt.ItemDataRole.UserRole) if current else None
        self.list.clear()
        for item in self.service.items:
            row = QListWidgetItem(icon_for(item.icon_id), item_label(self.service, item))
            row.setData(Qt.ItemDataRole.UserRole, item.id)
            row.setToolTip("<span>" + html.escape(item.name + "\n" + item.description).replace("\n", "<br>") + "</span>")
            self.list.addItem(row)
            if current_id == item.id:
                self.list.setCurrentItem(row)
        if self.service.items and self.list.currentItem() is None:
            self.list.setCurrentRow(0)
        if not self.service.items:
            self.status.setText("还没有快捷文本，先从管理中新增。")
        if self.service.problem:
            self.status.setText(self.service.problem)

    def copy_item(self, item: QListWidgetItem) -> None:
        result: CopyResult = self.service.copy(str(item.data(Qt.ItemDataRole.UserRole)), int(self.winId()))
        self.status.setText(f"已复制 · {result.name}" if result.succeeded else result.message)

    def open_manage(self) -> None:
        self.hide()
        self.manage()
