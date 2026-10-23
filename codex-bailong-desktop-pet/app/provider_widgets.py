"""Account settings and official WorkBuddy sign-in, using the existing panel style."""
import json
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QDialog
from PySide6.QtGui import QDesktopServices
from provider_accounts import PROVIDERS, WORKBUDDY_ORIGINS, snapshot_caption


class AccountSettings(QWidget):
    def __init__(self, monitor, state_dir, parent=None):
        super().__init__(parent)
        self.monitor, self.state_dir = monitor, state_dir
        self.login = None
        self.deepseek_login = None
        self.status_labels = {}
        self.account_forms={};self.manage_buttons={}
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        note = QLabel('每个平台一个账号，每5秒独立刷新。连接与断开立即生效；密钥加密保存在本机，不随设置备份导出。')
        note.setWordWrap(True)
        outer.addWidget(note)
        for key in ('glm', 'deepseek'):
            self.add_header(outer,key)
            box = QWidget()
            form = QFormLayout(box)
            form.setContentsMargins(0, 8, 0, 4)
            form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
            if key == 'glm':
                self.region = QComboBox()
                self.region.addItem('智谱国内站（个人订阅）', 'china')
                self.region.addItem('Z.ai 国际站（个人订阅）', 'international')
                self.region.setCurrentIndex(1 if monitor.config.get('glm', {}).get('region') == 'international' else 0)
                form.addRow('订阅站点', self.region)
            field = QLineEdit()
            field.setEchoMode(QLineEdit.EchoMode.Password)
            field.setMaxLength(4096)
            field.setAccessibleName(PROVIDERS[key]+' API Key')
            field.setPlaceholderText('输入套餐 API Key' if key == 'glm' else '输入 DeepSeek API Key')
            form.addRow('API Key', field)
            row = QHBoxLayout()
            save = QPushButton('保存并连接')
            save.clicked.connect(lambda checked=False, p=key, f=field: self.save_key(p, f))
            row.addWidget(save)
            clear = QPushButton('断开')
            clear.clicked.connect(lambda checked=False, p=key: self.disconnect(p))
            row.addWidget(clear)
            website = QPushButton('获取密钥')
            url = 'https://bigmodel.cn/usercenter/proj-mgmt/apikeys' if key == 'glm' else 'https://platform.deepseek.com/api_keys'
            website.clicked.connect(lambda checked=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            row.addWidget(website)
            form.addRow(row)
            if key=='deepseek':
                usage_login=QPushButton('登录 DeepSeek 用量页（Token）');usage_login.clicked.connect(self.open_deepseek)
                form.addRow(usage_login)
            outer.addWidget(box)
            self.account_forms[key]=box
            self.add_status(outer, key)
        self.add_header(outer,'workbuddy')
        workbuddy_form=QWidget();workbuddy_outer=QVBoxLayout(workbuddy_form);workbuddy_outer.setContentsMargins(0,0,0,0)
        row = QHBoxLayout()
        login = QPushButton('登录 / 重新登录 WorkBuddy')
        login.clicked.connect(self.open_workbuddy)
        row.addWidget(login)
        clear = QPushButton('断开')
        clear.clicked.connect(lambda: self.disconnect('workbuddy'))
        row.addWidget(clear)
        workbuddy_outer.addLayout(row);outer.addWidget(workbuddy_form);self.account_forms['workbuddy']=workbuddy_form
        self.add_status(outer, 'workbuddy')
        self.add_header(outer,'antigravity')
        antigravity_form=QWidget();antigravity_outer=QVBoxLayout(antigravity_form);antigravity_outer.setContentsMargins(0,0,0,0)
        note = QLabel('Antigravity 读取本机运行中的语言服务额度。请先在 Antigravity 中登录并打开一个项目；重登在原应用完成。')
        note.setWordWrap(True)
        antigravity_outer.addWidget(note)
        button = QPushButton('重新检测 Antigravity')
        button.clicked.connect(lambda: monitor.refresh('antigravity'))
        antigravity_outer.addWidget(button);outer.addWidget(antigravity_form);self.account_forms['antigravity']=antigravity_form
        self.add_status(outer, 'antigravity')
        self.message = QLabel()
        self.message.setWordWrap(True)
        outer.addWidget(self.message)
        monitor.changed.connect(self.update_status)
        for key in PROVIDERS:
            self.update_status(key, monitor.snapshots[key])
        for button in self.findChildren(QPushButton): button.setAutoDefault(False)

    def add_header(self,layout,key):
        row=QHBoxLayout();name=QLabel(PROVIDERS[key]);name.setStyleSheet('font-weight:600;');row.addWidget(name,1)
        button=QPushButton('管理');button.setCheckable(True);button.setFixedWidth(64)
        button.toggled.connect(lambda expanded,k=key,b=button:(self.account_forms[k].setVisible(expanded) if k in self.account_forms else None,b.setText('收起' if expanded else '管理')))
        row.addWidget(button);layout.addLayout(row);self.manage_buttons[key]=button

    def add_status(self, layout, key):
        label = QLabel()
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        label.setStyleSheet('font-size:10px;color:#706879;')
        self.status_labels[key] = label
        layout.addWidget(label)

    def update_status(self, key, snapshot):
        self.status_labels[key].setText(snapshot_caption(key, snapshot))
        configured=self.monitor.configured(key) if key!='antigravity' else bool(snapshot.get('observed'))
        button=self.manage_buttons[key]
        if not configured:
            button.setProperty('connected_once',False)
            if not button.isChecked():button.setChecked(True)
        elif configured and not button.property('connected_once'):
            button.setChecked(False);button.setProperty('connected_once',True)
        self.account_forms[key].setVisible(button.isChecked())
        button.setText('收起' if button.isChecked() else '管理')

    def save_key(self, key, field):
        secret = field.text().strip()
        if not secret:
            self.message.setText('请输入 API Key；已保存的密钥不会回显。')
            return
        config = dict(enabled=True)
        if key == 'glm': config['region'] = self.region.currentData()
        try: self.monitor.configure(key, config, secret)
        except (OSError, ValueError):
            self.message.setText('加密保存失败，输入仍保留，请重试。')
            return
        field.clear()
        self.message.setText(PROVIDERS[key]+' 已保存，正在查询。')

    def disconnect(self, key):
        try: self.monitor.configure(key, dict(enabled=False), '')
        except (OSError, ValueError):
            self.message.setText('断开失败，请重试。')
            return
        if key=='deepseek':self.monitor.secrets.put('deepseek_usage','')
        self.message.setText(PROVIDERS[key]+' 已断开并清除保存的凭据。')

    def shutdown(self):
        if self.login:self.login.shutdown()
        if self.deepseek_login:self.deepseek_login.shutdown()

    def open_deepseek(self):
        try:
            if self.deepseek_login is None:
                self.deepseek_login=DeepSeekUsageLogin(self.state_dir,self)
                self.deepseek_login.credentials.connect(self.save_deepseek_usage)
            self.deepseek_login.show();self.deepseek_login.raise_()
        except (ImportError,RuntimeError):self.message.setText('网页登录组件不可用。')

    def save_deepseek_usage(self,credentials):
        owner=self.window()
        # Embedded settings have a logical pet owner rather than a native parent.
        monitor=getattr(self.monitor.parent(),'provider_tokens',None)
        if monitor:
            monitor.usage_login(credentials)
            self.message.setText('DeepSeek 用量登录已加密保存，正在查询。')

    def open_workbuddy(self):
        try:
            if self.login is None:
                self.login = WorkBuddyLogin(self.state_dir, self)
                self.login.credentials.connect(self.save_workbuddy)
            self.login.show()
            self.login.raise_()
            self.login.view.reload()
        except (ImportError, RuntimeError):
            self.message.setText('网页登录组件不可用，请安装完整 PySide6 运行环境。')

    def save_workbuddy(self, credentials):
        if self.login:
            credentials=dict(credentials,headers=dict(credentials.get('headers',{})))
            credentials['headers']['user-agent']=self.login.profile.httpUserAgent()
        try: self.monitor.configure('workbuddy', dict(enabled=True), json.dumps(credentials))
        except (OSError, ValueError):
            self.message.setText('WorkBuddy 登录信息加密保存失败，请重试。')
            return
        self.message.setText('WorkBuddy 登录信息已保存，正在查询积分。')
        if self.login: self.login.note.setText('已连接登录信息，可以关闭此窗口。若查询提示失效，请重新登录。')


class WorkBuddyLogin(QDialog):
    credentials = Signal(object)

    def __init__(self, state_dir, parent=None):
        super().__init__(parent)
        from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineUrlRequestInterceptor
        from PySide6.QtWebEngineWidgets import QWebEngineView
        class Capture(QWebEngineUrlRequestInterceptor):
            captured = Signal(object)
            def __init__(self, parent):
                super().__init__(parent)
                self.last = None
            def interceptRequest(self, info):
                url = info.requestUrl()
                origin = url.scheme()+'://'+url.host()
                if origin not in WORKBUDDY_ORIGINS or not url.path().startswith(('/billing/', '/v2/')): return
                allowed = {'authorization', 'x-user-id', 'x-domain', 'x-enterprise-id', 'x-tenant-id', 'user-agent'}
                headers = {bytes(k).decode('ascii').lower(): bytes(v).decode('utf-8') for k, v in info.httpHeaders().items() if bytes(k).decode('ascii').lower() in allowed}
                if not headers.get('authorization', '').startswith('Bearer '): return
                value = dict(origin=origin, headers=headers)
                if value != self.last:
                    self.last = value
                    self.captured.emit(value)
        self.setWindowTitle('WorkBuddy · 登录账号')
        self.resize(1000, 740)
        layout = QVBoxLayout(self)
        self.note = QLabel('请在 WorkBuddy 官方网站登录，然后打开账号的积分页面，桌宠会连接该账号。登录失效后可在这里重新登录。')
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.cookie_values={}
        self.profile = QWebEngineProfile('bailong-workbuddy', self)
        self.profile.setPersistentStoragePath(str(state_dir/'workbuddy-browser'))
        self.profile.setCachePath(str(state_dir/'workbuddy-browser-cache'))
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.profile.cookieStore().cookieAdded.connect(self.cookie_added)
        self.profile.cookieStore().cookieRemoved.connect(self.cookie_removed)
        self.profile.cookieStore().loadAllCookies()
        self.capture = Capture(self.profile)
        self.capture.captured.connect(self.credentials.emit)
        self.profile.setUrlRequestInterceptor(self.capture)
        self.view = QWebEngineView(self)
        self.page = QWebEnginePage(self.profile, self.view)
        self.view.setPage(self.page)
        self.page.newWindowRequested.connect(lambda request: self.view.setUrl(request.requestedUrl()))
        layout.addWidget(self.view, 1)
        connect=QPushButton('已完成登录，连接当前账号');connect.setAutoDefault(False)
        connect.clicked.connect(self.connect_cookies);layout.addWidget(connect)
        self.view.loadFinished.connect(self.login_loaded)
        self.view.setUrl(QUrl('https://www.workbuddy.cn/console/account'))

    def cookie_added(self,cookie):
        if cookie.domain().lstrip('.') not in ('workbuddy.cn','www.workbuddy.cn'):return
        self.cookie_values[bytes(cookie.name())]=bytes(cookie.value())

    def cookie_removed(self,cookie):
        if cookie.domain().lstrip('.') not in ('workbuddy.cn','www.workbuddy.cn'):return
        self.cookie_values.pop(bytes(cookie.name()),None)

    def connect_cookies(self):
        if not self.cookie_values:
            self.note.setText('尚未获取登录状态，请先在页面中完成登录。');return
        cookies=b'; '.join(k+b'='+v for k,v in self.cookie_values.items()).decode('latin-1')
        self.credentials.emit(dict(origin='https://www.workbuddy.cn',headers={'cookie':cookies,'user-agent':self.profile.httpUserAgent()}))

    def login_loaded(self,success):
        if success and self.view.url().path().startswith('/console/account') and self.cookie_values:
            self.connect_cookies()

    def shutdown(self):
        self.view.stop();self.hide()
        self.page.deleteLater()
        self.profile.deleteLater()


class DeepSeekUsageLogin(QDialog):
    credentials=Signal(object)
    def __init__(self,state_dir,parent=None):
        super().__init__(parent)
        from PySide6.QtWebEngineCore import QWebEngineProfile,QWebEnginePage,QWebEngineUrlRequestInterceptor
        from PySide6.QtWebEngineWidgets import QWebEngineView
        class Capture(QWebEngineUrlRequestInterceptor):
            captured=Signal(object)
            def __init__(self,parent):super().__init__(parent);self.last=None
            def interceptRequest(self,info):
                url=info.requestUrl()
                if url.scheme()!='https' or url.host()!='platform.deepseek.com' or not url.path().startswith('/api/v0/usage/'):return
                allowed={'authorization','user-agent','x-client-platform','x-client-version'}
                headers={bytes(k).decode('ascii').lower():bytes(v).decode('utf-8') for k,v in info.httpHeaders().items() if bytes(k).decode('ascii').lower() in allowed}
                if not headers.get('authorization','').startswith('Bearer '):return
                if headers!=self.last:self.last=headers;self.captured.emit(dict(headers=headers))
        self.setWindowTitle('DeepSeek · 用量登录');self.resize(1000,740)
        layout=QVBoxLayout(self)
        note=QLabel('请在 DeepSeek 官方平台登录并打开用量页面。连接后可关闭此窗口。');note.setWordWrap(True);layout.addWidget(note)
        self.profile=QWebEngineProfile('bailong-deepseek',self)
        self.profile.setPersistentStoragePath(str(state_dir/'deepseek-browser'));self.profile.setCachePath(str(state_dir/'deepseek-browser-cache'))
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.capture=Capture(self.profile);self.capture.captured.connect(self.credentials.emit);self.profile.setUrlRequestInterceptor(self.capture)
        self.view=QWebEngineView(self);self.page=QWebEnginePage(self.profile,self.view);self.view.setPage(self.page)
        self.page.newWindowRequested.connect(lambda request:self.view.setUrl(request.requestedUrl()))
        layout.addWidget(self.view,1);self.view.setUrl(QUrl('https://platform.deepseek.com/usage'))
    def shutdown(self):
        self.view.stop();self.hide();self.page.deleteLater();self.profile.deleteLater()
