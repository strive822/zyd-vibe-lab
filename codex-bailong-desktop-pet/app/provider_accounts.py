"""Read-only account queries. Secrets never enter snapshots, logs or diagnostics."""
import json
import math
import ssl
import time
from itertools import chain
from datetime import datetime
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from urllib import request, error

PROVIDERS = {'glm': 'GLM', 'deepseek': 'DeepSeek', 'workbuddy': 'WorkBuddy', 'antigravity': 'Antigravity'}
INTERVAL_MS = 5000
WORKBUDDY_ORIGINS = ('https://www.workbuddy.cn', 'https://copilot.tencent.com')


class AccountError(Exception):
    def __init__(self, message, code='service', retry_after=0):
        super().__init__(message)
        self.code, self.retry_after = code, retry_after


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # Never forward account credentials to a redirected host.


def retry_seconds(value, now=None):
    now = time.time() if now is None else now
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        try:
            seconds = parsedate_to_datetime(value).timestamp() - now
        except (TypeError, ValueError, OverflowError):
            seconds = 60
    return max(5, seconds) if math.isfinite(seconds) else 60


def read_json(url, headers=None, body=None, timeout=10, local=False):
    from urllib.parse import urlsplit
    parts = urlsplit(url)
    if local and parts.hostname != '127.0.0.1':
        raise AccountError('本地查询地址无效', 'configuration')
    handlers = [NoRedirect()]
    if local:
        # Only the loopback LS uses a self-signed certificate; cloud TLS stays verified.
        handlers += [request.ProxyHandler({}), request.HTTPSHandler(context=ssl._create_unverified_context())]
    opener = request.build_opener(*handlers)
    data = None if body is None else json.dumps(body).encode('utf-8')
    req = request.Request(url, data=data, headers={'Accept': 'application/json', 'Content-Type': 'application/json', **(headers or {})})
    try:
        with opener.open(req, timeout=timeout) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise AccountError('服务返回数据过大', 'schema')
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise AccountError('服务返回格式暂不支持', 'schema')
        return value
    except error.HTTPError as exc:
        if exc.code in (401, 403):
            raise AccountError('登录已失效，请重新连接账号', 'authentication') from None
        if exc.code == 429:
            raise AccountError('服务限流，等待后自动重试', 'rate_limit', retry_seconds(exc.headers.get('Retry-After'))) from None
        raise AccountError('额度服务暂不可用（HTTP %s）' % exc.code, 'service') from None
    except (error.URLError, TimeoutError, OSError):
        raise AccountError('连接失败，稍后自动重试', 'network') from None
    except (ValueError, UnicodeError):
        raise AccountError('服务返回格式暂不支持', 'schema') from None


def number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError, OverflowError):
        return None


def timestamp(value):
    result = number(value)
    if result is not None:
        return result / 1000 if result > 100000000000 else result
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
        except (ValueError, OverflowError):
            pass
    return None


def decimal_text(value):
    try:
        result = Decimal(str(value))
        if result.is_finite():
            text = format(result, 'f')
            return text.rstrip('0').rstrip('.') if '.' in text else text
    except (InvalidOperation, ValueError):
        pass
    raise AccountError('服务没有提供有效数值', 'schema')


def unwrap(payload):
    if payload.get('success') is False or payload.get('code') not in (None, 0, 200, '0', '200'):
        code = str(payload.get('code', ''))
        if code in ('401', '403', '1001', '1002', '1003', '1004'):
            raise AccountError('登录已失效，请重新连接账号', 'authentication')
        raise AccountError('账户服务未能返回有效数据', 'service')
    data = payload.get('data', payload)
    if not isinstance(data, dict):
        raise AccountError('账户数据格式暂不支持', 'schema')
    return data


def parse_glm(payload):
    data = unwrap(payload)
    rows = []
    limits = data.get('limits')
    for item in limits if isinstance(limits, list) else []:
        if not isinstance(item, dict):
            continue
        used = number(item.get('percentage'))
        unit = item.get('unit')
        name = {3: '5小时', 6: '一周', 5: '月额度'}.get(unit)
        if name is None:
            name = 'MCP月额度' if item.get('type') == 'TIME_LIMIT' else '5小时' if item.get('type') == 'TOKENS_LIMIT' else str(item.get('type', '套餐额度'))[:40]
        rows.append(dict(name=name, remaining=100-used if used is not None and 0 <= used <= 100 else None,
                         resetsAt=timestamp(item.get('nextResetTime'))))
    if not rows or not any(r['remaining'] is not None for r in rows):
        raise AccountError('接口尚未提供套餐额度', 'schema')
    return dict(windows=rows, plan=str(data.get('level') or data.get('planName') or ''),
                expires_at=timestamp(data.get('expireTime') or data.get('expiresAt')))


def parse_deepseek(payload):
    rows, details = [], []
    for item in payload.get('balance_infos', []):
        if not isinstance(item, dict):
            continue
        currency = item.get('currency')
        if currency not in ('CNY', 'USD'):
            continue
        total = decimal_text(item.get('total_balance'))
        rows.append(dict(name='余额' if currency == 'CNY' else '美元余额', kind='amount', value_text=total,
                         unit='元' if currency == 'CNY' else 'USD', remaining=None, resetsAt=None))
        for field, label in [('total_balance', '总余额'), ('topped_up_balance', '充值余额'), ('granted_balance', '赠送余额')]:
            if item.get(field) is not None:
                details.append('%s：%s %s' % (label, decimal_text(item[field]), currency))
    if not rows:
        raise AccountError('接口没有提供账户余额', 'schema')
    return dict(windows=rows, details=details)


def parse_workbuddy(payload):
    data = unwrap(payload)
    packages = data.get('Packages')
    if not isinstance(packages, list):
        raise AccountError('积分接口格式已变化，请重新连接', 'schema')
    left = Decimal(0)
    total = Decimal(0)
    details = []
    for item in packages:
        if not isinstance(item, dict):
            raise AccountError('积分数据不完整', 'schema')
        remain_text = decimal_text(item.get('CycleRemainCapacity'))
        total_text = decimal_text(item.get('CycleTotalCapacity'))
        left += max(Decimal(0), Decimal(remain_text))
        total += max(Decimal(0), Decimal(total_text))
        details.append('%s：%s / %s 积分' % (str(item.get('PackageName') or item.get('PackageCode') or '积分包')[:80], remain_text, total_text))
    # An explicitly empty Packages array is a known zero, not a network failure.
    remaining = float(max(Decimal(0), min(Decimal(100), left / total * 100))) if total > 0 else None
    return dict(windows=[dict(name='剩余积分', kind='amount', value_text=decimal_text(left), unit='积分',
                              remaining=remaining, resetsAt=None)], details=details,
                plan=str(data.get('SubscriptionPackageName') or data.get('SubscriptionPackageCode') or ''))


def parse_antigravity(payload):
    status = payload.get('userStatus', payload)
    configs = status.get('cascadeModelConfigData', {}).get('clientModelConfigs', status.get('clientModelConfigs', []))
    rows = []
    for model in configs if isinstance(configs, list) else []:
        if not isinstance(model, dict):
            continue
        quota = model.get('quotaInfo') or {}
        # In protobuf JSON, a missing scalar fraction in a present quotaInfo is zero.
        fraction = number(quota.get('remainingFraction', 0)) if 'quotaInfo' in model else None
        if fraction is not None and 0 <= fraction <= 1:
            rows.append(dict(name=str(model.get('label') or '模型额度')[:100], remaining=fraction*100,
                             resetsAt=timestamp(quota.get('resetTime'))))
    if not rows:
        raise AccountError('Antigravity 尚未返回模型额度，请确认已登录', 'authentication')
    return dict(windows=rows, plan=str(status.get('planStatus', {}).get('planInfo', {}).get('planName') or ''))


class AntigravityReader:
    def __init__(self):
        self.connection = None

    def discover(self):
        import psutil
        for process in psutil.process_iter(['name', 'exe', 'cmdline']):
            try:
                info = process.info
                args = info.get('cmdline') or []
                name = (info.get('name') or '').lower()
                marker = ' '.join([info.get('exe') or '', *args]).lower()
                if not (('language_server' in name or 'language-server' in name) and 'antigravity' in marker):
                    continue
                def flag(key):
                    for i, arg in enumerate(args):
                        if arg == key and i+1 < len(args): return args[i+1]
                        if arg.startswith(key+'='): return arg.split('=', 1)[1]
                csrf = flag('--csrf_token')
                if not csrf:
                    continue
                ports = {c.laddr.port for c in process.net_connections('tcp') if c.status == psutil.CONN_LISTEN and c.laddr.ip in ('127.0.0.1', '::1', '0.0.0.0', '::')}
                for port in sorted(ports):
                    for scheme in ('https', 'http'):
                        yield scheme, port, csrf
            except (psutil.Error, OSError, ValueError):
                continue

    def __call__(self):
        candidates = chain([self.connection] if self.connection else [], self.discover())
        seen=set();deadline=time.monotonic()+12
        for connection in candidates:
            if time.monotonic()>deadline:break
            if connection in seen:continue
            seen.add(connection)
            scheme, port, csrf = connection
            try:
                payload = read_json('%s://127.0.0.1:%s/exa.language_server_pb.LanguageServerService/GetUserStatus' % (scheme, port),
                                    {'X-Codeium-Csrf-Token': csrf, 'Connect-Protocol-Version': '1'},
                                    {'metadata': {'ideName': 'antigravity', 'extensionName': 'antigravity', 'locale': 'en'}}, timeout=2, local=True)
                result = parse_antigravity(payload)
                self.connection = connection
                return result
            except AccountError:
                continue
        self.connection = None
        raise AccountError('请先启动 Antigravity 并登录账号', 'offline')


class AccountQueries:
    def __init__(self, state_dir=None):
        from antigravity_cloud import AntigravityQuotaReader
        self.antigravity = AntigravityQuotaReader(state_dir)

    def query(self, provider, config, secret):
        if provider == 'antigravity':
            return self.antigravity()
        if provider == 'workbuddy':
            try: credentials = json.loads(secret)
            except (TypeError, ValueError): raise AccountError('请先登录 WorkBuddy', 'configuration') from None
            origin = credentials.get('origin')
            if origin not in WORKBUDDY_ORIGINS:
                raise AccountError('WorkBuddy 登录站点无效', 'configuration')
            allowed = {'authorization', 'x-user-id', 'x-domain', 'x-enterprise-id', 'x-tenant-id', 'cookie', 'user-agent'}
            headers = {k: v for k, v in credentials.get('headers', {}).items() if k.lower() in allowed and isinstance(v, str)}
            # The website session is bound to its browser identity. Cookie-only
            # queries must keep the sign-in profile's UA as well as its cookies.
            headers.update({'Origin': origin, 'Referer': origin+'/console/account'})
            if not any(k.lower() in ('authorization', 'cookie') and v for k, v in headers.items()):
                raise AccountError('请先登录 WorkBuddy', 'configuration')
            return parse_workbuddy(read_json(origin+'/billing/meter/get-user-resource-summary', headers, {}))
        if not secret:
            raise AccountError('请在设置中连接账号', 'configuration')
        if provider == 'glm':
            origin = 'https://api.z.ai' if config.get('region') == 'international' else 'https://open.bigmodel.cn'
            return parse_glm(read_json(origin+'/api/monitor/usage/quota/limit', {'Authorization': secret, 'Accept-Language': 'zh-CN,zh'}))
        if provider == 'deepseek':
            return parse_deepseek(read_json('https://api.deepseek.com/user/balance', {'Authorization': 'Bearer '+secret}))
        raise AccountError('未知平台', 'configuration')


def snapshot_caption(provider, snapshot):
    pieces = [PROVIDERS[provider]]
    if snapshot.get('plan'): pieces.append(snapshot['plan'])
    if snapshot.get('observed'): pieces.append(time.strftime('%m/%d %H:%M:%S', time.localtime(snapshot['observed'])))
    if snapshot.get('error'):
        pieces.append(snapshot['error'])
        if snapshot.get('windows'): pieces.append('上次记录')
    elif snapshot.get('observed'):
        pieces.append('云端 · 每5秒刷新' if snapshot.get('source')=='cloud' else '每5秒刷新')
    else: pieces.append('未连接')
    return ' · '.join(pieces)
