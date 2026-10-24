"""Independent five-second polls, revision-safe results and bounded backoff."""
import copy
import json
import threading
import time
from PySide6.QtCore import QObject, QTimer, Signal
from desktop_core import atomic_json
from desktop_services import SecretStore
from provider_accounts import PROVIDERS, INTERVAL_MS, AccountQueries, AccountError


class ProviderMonitor(QObject):
    changed = Signal(str, object)
    completed = Signal(str, int, object, object)

    def __init__(self, state_dir, parent=None, query=None, start=True):
        super().__init__(parent)
        self.path = state_dir/'provider-accounts.json'
        self.secrets = SecretStore(state_dir/'provider-secrets.json')
        try: self.config = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError): self.config = {}
        if not isinstance(self.config, dict): self.config = {}
        self.snapshots = {key: {} for key in PROVIDERS}
        self.revisions = {key: 0 for key in PROVIDERS}
        self.inflight, self.next_due = set(), {}
        self.closed = False
        queries=None if query else AccountQueries(state_dir)
        self.query = query or queries.query
        if queries and start and self.configured('antigravity'):
            self.snapshots['antigravity']=queries.antigravity.cached()
        self.completed.connect(self._complete)
        self.timer = QTimer(self)
        self.timer.setInterval(INTERVAL_MS)
        self.timer.timeout.connect(self.refresh)
        if start:
            self.timer.start()
            QTimer.singleShot(0, self, self.refresh)

    def configured(self, key):
        if key == 'antigravity': return self.config.get(key, {}).get('enabled', True)
        return self.config.get(key, {}).get('enabled', False)

    def configure(self, key, config, secret=None):
        if key not in PROVIDERS: raise ValueError('未知平台')
        # Persist secrets first; do not advertise a connection that was not saved.
        if secret is not None: self.secrets.put(key, secret)
        new = copy.deepcopy(self.config)
        new[key] = {k: v for k, v in config.items() if k in ('enabled', 'region')}
        atomic_json(self.path, new)
        self.config = new
        self.revisions[key] += 1
        self.next_due.pop(key, None)
        # Never carry data from a previous account into the new account.
        self.snapshots[key] = {}
        self.changed.emit(key, {})
        self.refresh(key)

    def refresh(self, key=None):
        if self.closed: return
        for provider in [key] if key else PROVIDERS:
            if provider in self.inflight or not self.configured(provider) or time.monotonic() < self.next_due.get(provider, 0): continue
            revision = self.revisions[provider]
            config = copy.deepcopy(self.config.get(provider, {}))
            try: secret = '' if provider == 'antigravity' else self.secrets.get('deepseek_usage' if provider=='deepseek' and isinstance(self,ProviderTokenMonitor) else provider)
            except OSError:
                self._complete(provider, revision, None, AccountError('无法读取加密凭据，请重新连接', 'authentication'))
                continue
            self.inflight.add(provider)
            def run(p=provider, r=revision, c=config, s=secret):
                result = failure = None
                try: result = self.query(p, c, s)
                except AccountError as exc: failure = exc
                except Exception: failure = AccountError('查询失败，稍后自动重试', 'service')
                if not self.closed:
                    try: self.completed.emit(p, r, result, failure)
                    except RuntimeError: pass
            threading.Thread(target=run, name='BailongAccount-'+provider, daemon=True).start()

    def _complete(self, key, revision, result, failure):
        self.inflight.discard(key)
        if self.closed or revision != self.revisions[key]: return
        snapshot = dict(self.snapshots[key])
        if failure:
            if key=='antigravity' and hasattr(failure,'account_scope') and snapshot.get('account_scope')!=failure.account_scope:
                snapshot={}
            snapshot.update(error=str(failure), code=failure.code)
            delay = failure.retry_after or (30 if failure.code in ('authentication', 'configuration') else 5)
            self.next_due[key] = time.monotonic()+delay
        else:
            snapshot = dict(result, observed=time.time(), error='', code='ok')
            self.next_due.pop(key, None)
        self.snapshots[key] = snapshot
        self.changed.emit(key, copy.deepcopy(snapshot))

    def shutdown(self):
        self.closed = True
        self.timer.stop()


class ProviderTokenMonitor(ProviderMonitor):
    """Usage failures never interrupt balance/quota polling."""
    def __init__(self, accounts, state_dir, parent=None, start=True):
        from provider_tokens import ProviderTokenQueries
        self.usage_queries=ProviderTokenQueries(state_dir)
        super().__init__(state_dir,parent,query=self.usage_queries.query,start=False)
        self.accounts=accounts
        self.account_revisions=accounts.revisions.copy()
        accounts.changed.connect(self.account_changed)
        if start:self.timer.start();QTimer.singleShot(0,self,self.refresh)

    def configured(self,key):
        return self.accounts.configured(key)

    def account_changed(self,key,snapshot):
        self.config=copy.deepcopy(self.accounts.config)
        if self.account_revisions[key]!=self.accounts.revisions[key]:
            self.account_revisions[key]=self.accounts.revisions[key]
            self.revisions[key]+=1;self.next_due.pop(key,None);self.snapshots[key]={}
            self.changed.emit(key,{})
            self.refresh(key)

    def refresh(self,key=None):
        # DeepSeek usage uses a separate official-platform session, never its API key.
        self.config=copy.deepcopy(self.accounts.config)
        super().refresh(key)

    def usage_login(self,credentials):
        self.secrets.put('deepseek_usage',json.dumps(credentials))
        self.revisions['deepseek']+=1;self.next_due.pop('deepseek',None)
        self.snapshots['deepseek']={};self.changed.emit('deepseek',{})
        self.refresh('deepseek')

    def _complete(self,key,revision,result,failure):
        if self.closed or revision!=self.revisions[key]:
            self.inflight.discard(key);return
        if failure and not self.snapshots[key].get('observed'):
            self.snapshots[key]=dict(unavailable=True,error=str(failure))
        super()._complete(key,revision,result,failure)
