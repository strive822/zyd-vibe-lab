"""Read Antigravity's own Windows login; query quota without starting the app."""
import ctypes
import hashlib
import json
import mmap
import os
import re
import time
from itertools import chain
from pathlib import Path
from urllib import request,error,parse
from provider_accounts import AccountError,NoRedirect,read_json,retry_seconds,number,timestamp

HOSTS=('https://daily-cloudcode-pa.googleapis.com','https://cloudcode-pa.googleapis.com')
HEADERS={'User-Agent':'antigravity/2.0.0 win32/x64',
         'Client-Metadata':'{"ideType":"ANTIGRAVITY","platform":"WINDOWS_AMD64","pluginType":"GEMINI"}'}


def read_login():
    """Read exactly one application credential, never enumerate the vault."""
    if os.name!='nt':raise AccountError('当前系统不支持 Antigravity Windows 登录读取','configuration')
    from ctypes import wintypes
    class Credential(ctypes.Structure):
        _fields_=[('Flags',wintypes.DWORD),('Type',wintypes.DWORD),('TargetName',wintypes.LPWSTR),
                  ('Comment',wintypes.LPWSTR),('LastWritten',wintypes.FILETIME),('CredentialBlobSize',wintypes.DWORD),
                  ('CredentialBlob',ctypes.POINTER(ctypes.c_ubyte)),('Persist',wintypes.DWORD),
                  ('AttributeCount',wintypes.DWORD),('Attributes',ctypes.c_void_p),
                  ('TargetAlias',wintypes.LPWSTR),('UserName',wintypes.LPWSTR)]
    api=ctypes.WinDLL('advapi32',use_last_error=True)
    api.CredReadW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.POINTER(Credential))]
    api.CredReadW.restype=wintypes.BOOL;api.CredFree.argtypes=[ctypes.c_void_p]
    pointer=ctypes.POINTER(Credential)()
    if not api.CredReadW('gemini:antigravity',1,0,ctypes.byref(pointer)):
        raise AccountError('请先在 Antigravity 登录一次；以后关闭软件也可查询额度','configuration')
    try:
        value=pointer.contents
        if value.CredentialBlobSize>1024*1024:raise ValueError()
        data=json.loads(ctypes.string_at(value.CredentialBlob,value.CredentialBlobSize).decode('utf-8'))
        token=data.get('token')
        if not isinstance(token,dict) or not token.get('refresh_token'):raise ValueError()
        return token
    except (ValueError,TypeError,AttributeError,UnicodeError):
        raise AccountError('Antigravity 登录格式暂不支持，请重新登录','authentication') from None
    finally:api.CredFree(pointer)


def identity(token):
    return hashlib.sha256(token['refresh_token'].encode('utf-8')).hexdigest()


def client_candidates():
    """Discover installed app client constants in memory; never bundle them."""
    paths=[Path(os.environ.get('LOCALAPPDATA',''))/'Programs/antigravity/resources/bin/language_server.exe',
           Path(os.environ.get('LOCALAPPDATA',''))/'agy/bin/agy.exe']
    for path in paths:
        if not path.is_file():continue
        try:
            with path.open('rb') as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as data:
                ids=sorted(set(re.findall(rb'[0-9]{10,}-[a-z0-9]{16,}\.apps\.googleusercontent\.com',data)))
                secrets=sorted(set(re.findall(rb'GOCSPX-[A-Za-z0-9_-]{28}',data)))
            for cid in ids[:8]:
                for secret in secrets[:8]:yield cid.decode('ascii'),secret.decode('ascii')
        except (OSError,ValueError):continue


def refresh_token(refresh,candidate):
    fields=dict(client_id=candidate[0],client_secret=candidate[1],refresh_token=refresh,grant_type='refresh_token')
    req=request.Request('https://oauth2.googleapis.com/token',data=parse.urlencode(fields).encode('ascii'),
                        headers={'Content-Type':'application/x-www-form-urlencoded','Accept':'application/json'})
    try:
        with request.build_opener(NoRedirect()).open(req,timeout=10) as response:
            raw=response.read(1024*1024)
        payload=json.loads(raw)
    except error.HTTPError as exc:
        if exc.code==429:raise AccountError('登录服务限流，稍后自动重试','rate_limit',retry_seconds(exc.headers.get('Retry-After'))) from None
        try:code=json.loads(exc.read(4096)).get('error')
        except (ValueError,AttributeError):code=None
        if code in ('invalid_client','unauthorized_client'):return None
        if code=='invalid_grant':return None  # A token may belong to a different installed client candidate.
        raise AccountError('Antigravity 登录刷新失败','authentication') from None
    except (error.URLError,TimeoutError,OSError):
        raise AccountError('登录服务连接失败，稍后自动重试','network') from None
    except (ValueError,UnicodeError):raise AccountError('登录服务返回格式暂不支持','schema') from None
    if not isinstance(payload,dict) or not isinstance(payload.get('access_token'),str):
        raise AccountError('登录服务未返回有效凭据','schema')
    return payload


def parse_models(payload,plan=''):
    models=payload.get('models')
    if not isinstance(models,dict):raise AccountError('Antigravity 云端额度格式暂不支持','schema')
    rows=[]
    for key,value in models.items():
        if not isinstance(value,dict) or value.get('isInternal') or not value.get('displayName'):continue
        if key.startswith(('tab_','tab-')):continue
        quota=value.get('quotaInfo')
        if not isinstance(quota,dict):continue
        # A missing fraction is a protobuf zero only inside a present quotaInfo.
        fraction=number(quota.get('remainingFraction',0))
        if fraction is None or not 0<=fraction<=1:continue
        rows.append(dict(name=str(value['displayName'])[:100],remaining=fraction*100,resetsAt=timestamp(quota.get('resetTime'))))
    if not rows:raise AccountError('Antigravity 云端尚未提供有效额度','schema')
    rows=list({(r['name'],r['remaining'],r['resetsAt']):r for r in rows}.values())
    return dict(windows=rows,plan=plan,source='cloud',details=['Google 云端额度接口；不需要 Antigravity 运行。相同额度可能由多个模型共享，不相加。云端返回的档位不等同 Google One 订阅名称。'])


class AntigravityCloud:
    def __init__(self,state_dir=None,login_reader=None):
        self.login_reader=login_reader or read_login
        self.auth={};self.project=None;self.host=None;self.plan='';self.last_good=None
        self.store=None;self.cache_path=None
        if state_dir is not None:
            from desktop_services import SecretStore
            self.store=SecretStore(Path(state_dir)/'antigravity-cloud-auth.json')
            self.cache_path=Path(state_dir)/'antigravity-quota-cache.json'

    def restore(self,scope):
        if self.store:
            try:
                data=json.loads(self.store.get('oauth') or '{}')
                if isinstance(data,dict) and data.get('scope')==scope:self.auth=data
            except (OSError,ValueError):pass
        if self.cache_path:
            try:
                value=json.loads(self.cache_path.read_text(encoding='utf-8'))
                if value.get('scope')==scope and isinstance(value.get('snapshot'),dict):self.last_good=value['snapshot']
            except (OSError,ValueError,AttributeError):pass

    def token(self,original,scope,force=False):
        if self.auth.get('scope')!=scope:
            self.auth={};self.project=None;self.host=None;self.plan='';self.last_good=None;self.restore(scope)
        expires=timestamp(original.get('expiry')) or 0
        if not force and self.auth.get('access') and self.auth.get('expires',0)>time.time()+60:return self.auth['access']
        if not force and original.get('access_token') and expires>time.time()+60:
            self.auth=dict(scope=scope,access=original['access_token'],expires=expires)
            return self.auth['access']
        prefix=[tuple(self.auth['client'])] if self.auth.get('client') else []
        refresh=self.auth.get('refresh') or original['refresh_token']
        seen=set()
        for candidate in chain(prefix,client_candidates()):
            if candidate in seen:continue
            if len(seen)>=16:break
            seen.add(candidate)
            result=refresh_token(refresh,candidate)
            if result:
                self.auth=dict(scope=scope,access=result['access_token'],expires=time.time()+max(0,min(86400,number(result.get('expires_in')) or 3600)),
                               refresh=result.get('refresh_token') or refresh,client=candidate)
                if self.store:
                    try:self.store.put('oauth',json.dumps(self.auth))
                    except OSError:pass  # A working read-only query does not depend on cache writes.
                return self.auth['access']
        raise AccountError('Antigravity 登录失效或客户端已变化，请在原应用重新登录','authentication')

    def __call__(self):
        try:original=self.login_reader()
        except AccountError as exc:
            exc.account_scope='';raise
        scope=identity(original)
        try:return self.query_account(original,scope)
        except AccountError as exc:
            exc.account_scope=scope;raise

    def query_account(self,original,scope):
        access=self.token(original,scope)
        for attempt in range(2):
            try:
                result=dict(self.fetch(access),account_scope=scope)
                self.last_good=dict(result,observed=time.time(),error='',code='ok')
                if self.cache_path:
                    from desktop_core import atomic_json
                    try:atomic_json(self.cache_path,dict(scope=scope,snapshot=self.last_good))
                    except OSError:pass
                return result
            except AccountError as exc:
                if exc.code!='authentication' or attempt:raise
                self.project=None;self.host=None;access=self.token(original,scope,force=True)

    def fetch(self,access):
        headers=dict(HEADERS,Authorization='Bearer '+access)
        hosts=([self.host] if self.host else [])+[host for host in HOSTS if host!=self.host]
        failure=None
        for host in hosts:
            try:
                if self.project is None:
                    context=read_json(host+'/v1internal:loadCodeAssist',headers,{'metadata':{'ideType':'ANTIGRAVITY','platform':'WINDOWS_AMD64','pluginType':'GEMINI'}})
                    project=context.get('cloudaicompanionProject')
                    if isinstance(project,dict):project=project.get('id')
                    if not isinstance(project,str) or not project:
                        raise AccountError('Antigravity 未返回账号项目，请在原应用完成首次登录','configuration')
                    self.project=project
                    tier=context.get('paidTier') or context.get('currentTier') or {}
                    self.plan=str(tier.get('name') or tier.get('id') or '')[:100]
                payload=read_json(host+'/v1internal:fetchAvailableModels',headers,{'project':self.project})
                result=parse_models(payload,self.plan);self.host=host
                return result
            except AccountError as exc:
                failure=exc;self.project=None
                if exc.code in ('rate_limit','authentication'):raise
        raise failure or AccountError('云端额度连接失败','network')


class AntigravityQuotaReader:
    def __init__(self,state_dir=None,cloud=None,local=None):
        from provider_accounts import AntigravityReader
        self.cloud=cloud or AntigravityCloud(state_dir)
        self.local=local or AntigravityReader()

    def cached(self):
        try:
            scope=identity(self.cloud.login_reader());self.cloud.restore(scope)
            value=self.cloud.last_good
            if not isinstance(value,dict) or not isinstance(value.get('windows'),list):return {}
            observed=number(value.get('observed'))
            if observed is None or not 0<observed<=time.time()+60:return {}
            rows=value['windows']
            if not rows or any(not isinstance(r,dict) or number(r.get('remaining')) is None or not 0<=r['remaining']<=100 for r in rows):return {}
            return dict(value,account_scope=scope,code='cached',stale=True,error='已恢复上次额度，正在云端刷新')
        except (AccountError,OSError,ValueError,TypeError):return {}

    def __call__(self):
        try:return self.cloud()
        except AccountError as failure:
            if failure.code=='rate_limit':raise
            try:
                value=self.local()
                return dict(value,account_scope=getattr(failure,'account_scope',''),source='local',details=['本机 Antigravity 额度；云端暂不可用。'])
            except AccountError:raise failure from None
