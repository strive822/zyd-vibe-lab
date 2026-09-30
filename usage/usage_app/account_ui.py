"""Local single-account controls; credentials are entered only by the user."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget

from palette_visual import Palette

from .credentials import CredentialError
from .models import ERROR_MESSAGES, Provider, Status
from .messages import product_message
from .runtime import UsageRuntime
from .storage import StorageError


class AccountPage(QWidget):
    def __init__(self, runtime: UsageRuntime, theme: Palette, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.runtime = runtime
        self.fields: dict[Provider, QLineEdit] = {}
        self.statuses: dict[Provider, QLabel] = {}
        self.buttons: dict[Provider, QPushButton] = {}
        self.feedbacks: dict[Provider, QLabel] = {}
        self.theme = theme
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        root.setSpacing(14)
        for provider, name, color in ((Provider.CODEX, "Codex", theme.codex.name()), (Provider.GLM, "GLM 国内个人版", theme.glm.name()), (Provider.DEEPSEEK, "DeepSeek", theme.balance.name())):
            heading = QLabel(name)
            heading.setStyleSheet(f"font-size: 12pt; font-weight: 600; color: {color}; padding-top: 5px;")
            root.addWidget(heading)
            state = QLabel()
            state.setObjectName("muted")
            state.setWordWrap(True)
            state.setTextFormat(Qt.TextFormat.PlainText)
            self.statuses[provider] = state
            root.addWidget(state)
            if provider == Provider.CODEX:
                note = QLabel("使用本机官方 Codex 的登录状态，仅查询额度。登录或更换订阅账号请在官方应用中完成。")
                note.setWordWrap(True)
                root.addWidget(note)
                button = QPushButton()
                button.clicked.connect(self.toggle_codex)
                self.buttons[provider] = button
                root.addWidget(button)
            else:
                field = QLineEdit()
                field.setEchoMode(QLineEdit.EchoMode.Password)
                field.setPlaceholderText("输入新的 API Key")
                field.setAccessibleName(name + " API Key，不回填现有密钥")
                self.fields[provider] = field
                form = QFormLayout()
                form.addRow("API Key", field)
                root.addLayout(form)
                row = QHBoxLayout()
                save = QPushButton("保存并连接")
                save.setObjectName("primary")
                save.clicked.connect(lambda checked=False, provider=provider: self.connect_key(provider))
                disconnect = QPushButton("断开连接")
                disconnect.clicked.connect(lambda checked=False, provider=provider: self.disconnect_account(provider))
                self.buttons[provider] = disconnect
                row.addWidget(save)
                row.addWidget(disconnect)
                row.addStretch()
                root.addLayout(row)
            feedback = QLabel()
            feedback.setObjectName("status")
            feedback.setTextFormat(Qt.TextFormat.PlainText)
            feedback.setWordWrap(True)
            feedback.hide()
            root.addWidget(feedback)
            self.feedbacks[provider] = feedback
        self.message = QLabel()
        self.message.setObjectName("status")
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        self.message.setWordWrap(True)
        root.addWidget(self.message)
        self.cleanup = QPushButton("重试旧本机数据清理")
        self.cleanup.clicked.connect(self.retry_cleanup)
        root.addWidget(self.cleanup)
        note = QLabel("每家仅连接一个账号。密钥只保存在 Windows 凭据管理器，配置、快照和日志不保存密钥。查询失败时保留上次成功数据；尚未核验的字段会明确标注。")
        note.setObjectName("muted")
        note.setWordWrap(True)
        root.addWidget(note)
        root.addStretch()
        runtime.changed.connect(self.update_states)
        runtime.storage_failed.connect(lambda message: self.message.setText(product_message(message)))
        self.update_states()

    def _feedback(self, provider: Provider, message: str | Exception, *, failed: bool = False) -> None:
        label = self.feedbacks[provider]
        label.setText(product_message(message))
        label.setStyleSheet("color: " + (self.theme.low.name() if failed else "#686c63") + ";")
        label.show()
        def ensure_visible() -> None:
            owner = self.parentWidget()
            while owner is not None and not isinstance(owner, QScrollArea):
                owner = owner.parentWidget()
            if isinstance(owner, QScrollArea):
                owner.ensureWidgetVisible(label, 16, 24)
        QTimer.singleShot(0, ensure_visible)

    def update_states(self) -> None:
        for provider, label in self.statuses.items():
            state = self.runtime.states.get(provider)
            if state is None or not state.account.enabled:
                text = "尚未连接"
            elif state.error:
                text = ERROR_MESSAGES[state.error]
            elif state.status == Status.LOADING:
                text = "正在读取额度"
            elif provider != Provider.CODEX and not state.account.credential_ref:
                text = "尚未配置 API Key"
            elif state.status == Status.FRESH:
                text = "官方只读数据已更新"
            elif state.snapshot:
                text = "保留上次成功数据，等待更新"
            else:
                text = "已启用，等待查询"
            label.setText(text)
            if provider == Provider.CODEX:
                self.buttons[provider].setText("停用 Codex 查询" if state and state.account.enabled else "启用本机 Codex")
            else:
                self.buttons[provider].setEnabled(bool(state and state.account.enabled and state.account.credential_ref))
        self.cleanup.setVisible(bool(self.runtime.accounts.cleanup_warning))
        if self.runtime.accounts.cleanup_warning:
            self.message.setText(self.runtime.accounts.cleanup_warning)

    def connect_key(self, provider: Provider) -> None:
        field = self.fields[provider]
        if not field.text().strip():
            self._feedback(provider, "请先填写 API Key。", failed=True)
            field.setFocus()
            return
        try:
            self.runtime.accounts.connect_key(provider, field.text().strip())
            self.runtime.reload_accounts()
            self.runtime.refresh_now()
            self._feedback(provider, self.runtime.accounts.cleanup_warning or "账号已保存，正在核验只读数据。")
        except (StorageError, CredentialError, ValueError) as error:
            self._feedback(provider, error, failed=True)
        finally:
            field.clear()
        self.update_states()

    def disconnect_account(self, provider: Provider) -> None:
        try:
            self.runtime.accounts.disconnect(provider)
            self.runtime.reload_accounts()
            self.fields[provider].clear()
            self._feedback(provider, self.runtime.accounts.cleanup_warning or "已断开此平台；其他平台和快捷文本保持可用。")
        except (StorageError, CredentialError) as error:
            self._feedback(provider, error, failed=True)
        self.update_states()

    def toggle_codex(self) -> None:
        current = self.runtime.states.get(Provider.CODEX)
        try:
            self.runtime.accounts.set_codex_enabled(not bool(current and current.account.enabled))
            self.runtime.reload_accounts()
            self.runtime.refresh_now()
            self._feedback(Provider.CODEX, "Codex 查询设置已保存。")
        except StorageError as error:
            self._feedback(Provider.CODEX, error, failed=True)

    def retry_cleanup(self) -> None:
        success = self.runtime.accounts.retry_cleanup()
        self.message.setText("旧本机数据已清理。" if success else self.runtime.accounts.cleanup_warning or "清理未完成，请稍后重试。")
        self.update_states()
