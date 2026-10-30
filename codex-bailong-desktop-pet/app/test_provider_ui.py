import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
import tempfile
import time
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication,QEvent,Qt
from PySide6.QtWidgets import QApplication,QToolButton,QLabel,QLineEdit
from compact_bubble import CompactBubble
from quota_summary import QuotaSummary
from provider_accounts import parse_deepseek,parse_antigravity
from provider_monitor import ProviderMonitor
from provider_widgets import AccountSettings,WorkBuddyLogin

app=QApplication.instance() or QApplication([])

def settle():
    app.processEvents()
    for window in app.topLevelWidgets():
        transition=getattr(window,'size_transition',None)
        if transition:transition.complete()
    app.processEvents()


class ProviderUiTests(unittest.TestCase):
    def test_system_notifications_stay_off_before_any_shell_access(self):
        from types import SimpleNamespace
        from desktop_core import normalized
        from enhanced import EnhancedPet
        settings=normalized({'notifications':False})
        self.assertFalse(normalized({})['notifications'])
        pet=SimpleNamespace(settings=settings,notify_history=[])
        EnhancedPet.notify(pet,'test-only notification','test-only body')
        self.assertEqual(pet.notify_history,[])

    def setUp(self):
        self.b=CompactBubble()
        self.b.windows=[dict(name='5小时',remaining=75)]
        self.b.redraw();self.b.show();settle()

    def tearDown(self):
        self.b.close();self.b.deleteLater();settle()

    def test_platform_menu_switches_without_changing_original_card_size(self):
        before=self.b.size()
        button=self.b.findChild(QToolButton,'account_platform')
        self.assertEqual([a.text() for a in button.menu().actions()],['Codex','GLM','DeepSeek','WorkBuddy','Antigravity'])
        self.b.provider_snapshots['deepseek']=dict(parse_deepseek({'balance_infos':[{'currency':'CNY','total_balance':'123.45'}]}),observed=time.time())
        button.menu().actions()[2].trigger();settle()
        self.assertEqual(self.b.account_platform,'deepseek')
        self.assertEqual(self.b.size(),before)
        card=next(c for c in self.b.findChildren(QuotaSummary) if c.isVisible())
        self.assertEqual(card.items[0]['display'],'123.45 元')
        self.assertEqual(self.b.windows[0]['remaining'],75)  # Codex data stays independent.
        self.b.select_account_platform('codex');settle()
        card=next(c for c in self.b.findChildren(QuotaSummary) if c.isVisible())
        self.assertEqual(card.items[0]['display'],'75%')

    def test_antigravity_details_include_every_model_not_only_first_two(self):
        self.b.provider_snapshots['antigravity']=parse_antigravity({'clientModelConfigs':[
            dict(label='Model '+str(i),quotaInfo=dict(remainingFraction=.5)) for i in range(6)]})
        self.b.select_account_platform('antigravity');settle()
        self.b.show_quota_details();settle()
        text='\n'.join(w.text() for w in self.b.details_tabs.findChildren(QLabel))
        for i in range(6):self.assertIn('Model '+str(i),text)

    def test_model_filter_and_codex_quota_history_survive_page_switch(self):
        from daily_report import DailyReport
        from desktop import DesktopPet
        from types import SimpleNamespace
        from test_daily_report import sample
        self.b.token_snapshot=sample()
        history={'cycles':[], 'migration':{'complete':True}}
        self.b.token_snapshot['quota_history']=history
        self.b.provider_token_snapshots['glm']=dict(report=dict(
            day='2026-10-18',models_end='2026-10-18',
            daily_models=[dict(day='2026-10-18',model='glm-test',total=123,input=100,output=23,known=True)]))
        report=DailyReport(self.b)
        self.b.report=report
        try:
            report.set_snapshot(self.b.report_snapshot())
            report.set_page('models');report.set_platform('glm')
            self.assertEqual(report.report['daily_models'][0]['model'],'glm-test')
            report.set_page('cycle')
            self.assertIs(report.snapshot['quota_history'],history)
            self.assertNotIn('glm-test',str(report.snapshot['report']['daily_models']))
            report.set_page('models')
            self.assertEqual(report.platform_filter,'glm')
            self.assertEqual(report.report['daily_models'][0]['model'],'glm-test')
            with patch.object(report,'open'):
                DesktopPet.open_quota_comparison(SimpleNamespace(bubble=self.b))
            self.assertIn('glm',report.full_snapshot.get('platform_snapshots',{}))
            report.set_page('models')
            self.assertEqual(report.report['daily_models'][0]['model'],'glm-test')
        finally:report.close();report.deleteLater();settle()

    def test_chat_removed_from_navigation_shortcuts_and_runtime(self):
        from quick_actions import ACTIONS,action_info
        from desktop import DesktopPet
        from PySide6.QtWidgets import QMenu
        self.assertNotIn('chat',[a[0] for a in ACTIONS])
        self.assertEqual(action_info('chat')[0],'refresh')
        self.assertFalse(hasattr(DesktopPet,'open_chat'))
        self.assertFalse(hasattr(DesktopPet,'open_chat_service'))
        self.b.show_quota_details();settle()
        self.assertIsNone(self.b.findChild(QToolButton,'bubble_chat'))
        self.assertIsNotNone(self.b.findChild(QToolButton,'bubble_settings'))

    def test_account_keys_are_masked_and_encrypted_on_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            monitor=ProviderMonitor(Path(tmp),query=lambda *args:dict(windows=[]),start=False)
            settings=AccountSettings(monitor,Path(tmp))
            field=next(w for w in settings.findChildren(QLineEdit) if 'DeepSeek' in w.accessibleName())
            self.assertEqual(field.echoMode(),QLineEdit.EchoMode.Password)
            field.setText('test-only-secret')
            settings.save_key('deepseek',field)
            self.assertEqual(field.text(),'')
            self.assertEqual(monitor.secrets.get('deepseek'),'test-only-secret')
            self.assertNotIn('test-only-secret',(Path(tmp)/'provider-secrets.json').read_text())
            self.assertNotIn('test-only-secret',(Path(tmp)/'provider-accounts.json').read_text())
            settings.disconnect('deepseek')
            self.assertEqual(monitor.secrets.get('deepseek'),'')
            monitor.shutdown();settings.deleteLater();settle()

    def test_workbuddy_browser_starts_at_account_login_and_releases_profile(self):
        # Chromium flushes profile files asynchronously. An isolated interpreter
        # verifies the real persistent profile and releases its OS handles before
        # the parent removes the temporary directory, including on slow CI hosts.
        with tempfile.TemporaryDirectory() as tmp:
            code = textwrap.dedent('''
                import sys
                from pathlib import Path
                from unittest.mock import patch
                from PySide6.QtCore import QCoreApplication, QEvent
                from PySide6.QtWidgets import QApplication
                from PySide6.QtWebEngineWidgets import QWebEngineView
                from provider_widgets import WorkBuddyLogin
                app = QApplication([])
                with patch.object(QWebEngineView, 'setUrl') as navigate:
                    login = WorkBuddyLogin(Path(sys.argv[1]))
                    assert navigate.call_args.args[0].toString() == 'https://www.workbuddy.cn/console/account'
                    captured = []
                    login.credentials.connect(captured.append)
                    login.cookie_values = {b'session': b'test-only-cookie'}
                    login.connect_cookies()
                    assert captured[0]['headers']['cookie'] == 'session=test-only-cookie'
                    login.shutdown()
                    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
                    app.processEvents()
                    login.deleteLater()
                    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
                    app.processEvents()
            ''')
            environment = dict(os.environ)
            environment['PYTHONPATH'] = os.pathsep.join([str(Path(__file__).resolve().parent), environment.get('PYTHONPATH', '')])
            result = subprocess.run([sys.executable, '-c', code, tmp], env=environment,
                                    capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__=='__main__':unittest.main()
