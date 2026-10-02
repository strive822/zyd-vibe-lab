"""Account UI uses isolated fake secrets; never queries or screenshots real keys."""
from __future__ import annotations

from _paths import EVIDENCE

import json
import tempfile
from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QLineEdit

from usage_app.account_ui import AccountPage
from usage_app.accounts import AccountStore
from usage_app.desktop import DesktopLeaf
from usage_app.models import Provider
from usage_app.runtime import UsageRuntime
from usage_app.storage import StorageError


class FakeSecrets:
    def __init__(self):
        self.values = {}

    def write(self, reference, text):
        self.values[reference] = text

    def read(self, reference):
        return self.values.get(reference)

    def delete(self, reference):
        self.values.pop(reference, None)


def pump(milliseconds=120):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def main() -> int:
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    out = Path(EVIDENCE / "m5") / str(round(app.primaryScreen().devicePixelRatio() * 100))
    out.mkdir(parents=True, exist_ok=True)
    checks = []
    with tempfile.TemporaryDirectory(prefix="duizhaoye-accounts-check-") as directory:
        runtime = UsageRuntime(Path(directory))
        runtime.stop()
        secrets = FakeSecrets()
        runtime.accounts = AccountStore(Path(directory), secrets)
        leaf = DesktopLeaf(runtime, reduced_motion=True)
        leaf._pulse.stop()
        leaf.show()
        leaf._open_settings("accounts")
        panel = leaf.text_settings
        page = panel.findChild(AccountPage)
        assert page is not None
        pump()
        panel.grab().save(str(out / "accounts-unconfigured.png"))
        for provider in (Provider.GLM, Provider.DEEPSEEK):
            assert page.fields[provider].echoMode() == QLineEdit.EchoMode.Password
            page.fields[provider].setText("synthetic-not-a-real-key")
            page.connect_key(provider)
            assert not page.fields[provider].text()
            assert runtime.states[provider].account.credential_ref
        assert len(secrets.values) == 2
        assert "synthetic-not" not in runtime.accounts.store.path.read_text(encoding="utf-8")
        panel.grab().save(str(out / "accounts-configured-reference.png"))
        checks.append("masked input saves only owned references; key cleared without backfill")
        glm = runtime.states[Provider.GLM].account
        page.disconnect_account(Provider.DEEPSEEK)
        assert runtime.states[Provider.GLM].account == glm
        assert not runtime.states[Provider.DEEPSEEK].account.enabled
        checks.append("disconnect affects only its provider")
        original = runtime.accounts.save
        def fail(accounts, **kwargs):
            raise StorageError("保存失败，原配置已保留")
        runtime.accounts.save = fail
        page.fields[Provider.GLM].setText("synthetic-replacement")
        page.connect_key(Provider.GLM)
        assert runtime.states[Provider.GLM].account == glm
        assert len(secrets.values) == 1
        pump()
        assert page.feedbacks[Provider.GLM].isVisible()
        assert panel.rect().contains(page.feedbacks[Provider.GLM].mapTo(panel, page.feedbacks[Provider.GLM].rect().center()))
        panel.grab().save(str(out / "accounts-save-error.png"))
        runtime.accounts.save = original
        checks.append("save failure retains previous account and removes staged fake credential")
        page.toggle_codex()
        assert not runtime.states[Provider.CODEX].account.enabled
        page.toggle_codex()
        assert runtime.states[Provider.CODEX].account.enabled
        panel.resize(560, 480)
        pump()
        panel.grab().save(str(out / "accounts-small.png"))
        checks.append("local Codex toggle and small scrolling layout")
        leaf.reminders.stop()
        leaf.snippets.stop()
        panel.hide()
        leaf.tray.hide()
        leaf._quitting = True
        leaf.close()
    report = {"passed": len(checks), "checks": checks, "nativeDpr": app.primaryScreen().devicePixelRatio(),
              "boundary": "Native Qt account form, isolated fake credential adapter and stopped transport. This is not real GLM/DeepSeek authentication proof."}
    (out / "account-native-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
