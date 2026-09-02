# -*- coding: utf-8 -*-
"""行情数据层：多源行情获取（东财主源 + 腾讯/新浪回退）、清洗与口径判定。

职责边界：
  - 只负责“拿到干净的数据”，不做任何模型计算。
  - 任何失败都抛出带明确中文信息的异常，绝不返回 0 / 伪数据 / 部分数据。
  - 每个资产按 AssetConfig.sources 顺序尝试：历史与报价齐全才算成功；
    历史可用但报价缺失时记为“降级候选”（指数类可回退用最近已完成收盘价）。
"""
from __future__ import annotations

import json
import math
import re
import threading
from dataclasses import dataclass
from datetime import date, datetime, time
from time import monotonic as _monotonic
from zoneinfo import ZoneInfo

import requests

from app.config import (
    HTTP_HEADERS,
    HTTP_TIMEOUT,
    HISTORY_DAYS,
    KLINE_HOSTS,
    KLINE_REQUEST_BARS,
    QUOTE_HOSTS,
    UT_TOKEN,
    AssetConfig,
    SourceSpec,
)

SOURCE_EASTMONEY = "东方财富"
SOURCE_TENCENT = "腾讯"
SOURCE_SINA = "新浪财经"

_SINJA_HEADERS = {"Referer": "https://finance.sina.com.cn"}


class MarketDataError(Exception):
    """行情数据无法可靠获得的基类。"""


class DataSourceError(MarketDataError):
    """数据源网络/接口失败。"""


class DataQualityError(MarketDataError):
    """数据源返回了，但数据不合规（为空/不足/无效）。"""


@dataclass(frozen=True)
class AssetData:
    key: str
    name: str
    bars: tuple[tuple[date, float], ...]  # 已清洗、按日期升序的全部日线
    quote_price: float | None             # 最新报价（获取失败为 None）
    quote_time: datetime | None           # 最新报价时间（带时区）
    source: str = SOURCE_EASTMONEY


# ---------------------------------------------------------------------------
# 清洗与口径（公开函数，供单元测试直接验证）
# ---------------------------------------------------------------------------

def clean_bars(raw_pairs) -> tuple[tuple[date, float], ...]:
    """清洗原始日线：丢弃 NaN/Infinity/非正收盘与非法日期；重复日期保留后出现的；按日期升序。"""
    merged: dict[date, float] = {}
    for d, c in raw_pairs:
        try:
            c = float(c)
        except (TypeError, ValueError):
            continue
        if not isinstance(d, date) or isinstance(d, datetime):
            continue
        if not math.isfinite(c) or c <= 0:
            continue
        merged[d] = c  # 重复日期 → 后者覆盖前者
    return tuple(sorted(merged.items()))


def select_completed_bars(
    bars: tuple[tuple[date, float], ...],
    now: datetime,
    close_time: time | None,
) -> list[tuple[date, float]]:
    """筛选“已完成交易日”的K线（保持升序）。

    规则：
      bar 日期 < 当地今天                     → 完整
      bar 日期 == 当地今天 且 now >= close_time → 完整（当日已收盘）
      bar 日期 == 当地今天 且 close_time 为 None → 永不完整（现货黄金无收盘概念）
      bar 日期 > 当地今天                     → 异常数据，丢弃
    由此保证：未收盘的盘中价格永远不会进入 SMA800。
    """
    today = now.date()
    now_time = now.time()
    completed: list[tuple[date, float]] = []
    for d, c in bars:
        if d < today:
            completed.append((d, c))
        elif d == today and close_time is not None and now_time >= close_time:
            completed.append((d, c))
    return completed


def format_price_time(price_time: datetime, cfg: AssetConfig) -> str:
    """行情时间展示文本，例如 '2026-09-01 16:00 ET'。"""
    return f"{price_time:%Y-%m-%d %H:%M} {cfg.tz_label}"


# ---------------------------------------------------------------------------
# HTTP 基础（多 URL 依次尝试；每个 URL 先直连再走系统代理）
# ---------------------------------------------------------------------------

def _http_get(urls: tuple[str, ...], label: str, extra_headers=None) -> bytes:
    """依次尝试多个 URL；每个 URL 先直连（绕过系统代理）再走系统代理。

    说明：requests 在 Windows 上会读取注册表里的系统代理，本机实测代理会导致
    东财接口 ProxyError，因此国内数据源必须优先直连。
    全部失败抛 DataSourceError。
    """
    errors: list[str] = []
    headers = {**HTTP_HEADERS, **(extra_headers or {})}
    for url in urls:
        for trust_env in (False, True):
            try:
                with requests.Session() as session:
                    session.trust_env = trust_env
                    resp = session.get(url, headers=headers, timeout=HTTP_TIMEOUT)
                resp.raise_for_status()
                if not resp.content:
                    raise ValueError("空响应体")
                return resp.content
            except Exception as exc:  # noqa: BLE001 - 数据源异常必须逐层兜底
                errors.append(f"{'代理' if trust_env else '直连'}:{type(exc).__name__}")
                _sleep(0.3)
    raise DataSourceError(
        f"当前无法完成计算：{label}获取失败（{'；'.join(errors[-2:])}）。"
    )


def _sleep(seconds: float) -> None:
    from time import sleep

    sleep(seconds)


def _positive_float(value) -> float | None:
    """解析正的有限浮点数，失败返回 None。"""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v > 0 else None


# ---------------------------------------------------------------------------
# 数据源一：东方财富
# ---------------------------------------------------------------------------

def _fetch_eastmoney(cfg: AssetConfig, spec: SourceSpec) -> AssetData:
    """东财日线（fields2=f51 日期, f53 收盘）+ 最新报价（f43/f86）。"""
    kline_urls = tuple(
        f"{host}/api/qt/stock/kline/get?secid={spec.symbol}&ut={UT_TOKEN}"
        "&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f53"
        f"&klt=101&fqt=0&beg=0&end=20500101&lmt={KLINE_REQUEST_BARS}"
        for host in KLINE_HOSTS
    )
    payload = json.loads(_http_get(kline_urls, f"{cfg.name}[东财]历史行情"))
    data = (payload or {}).get("data") or {}
    klines = data.get("klines")
    if not isinstance(klines, list) or not klines:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}历史行情返回为空。")

    raw_pairs: list[tuple[date, float]] = []
    for item in klines:
        parts = str(item).split(",")
        if len(parts) < 2:
            continue
        try:
            d = date.fromisoformat(parts[0].strip())
        except ValueError:
            continue
        raw_pairs.append((d, parts[1]))

    bars = clean_bars(raw_pairs)
    if not bars:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}日线数据全部无效。")

    # 报价通道
    quote_price: float | None = None
    quote_time: datetime | None = None
    try:
        quote_urls = tuple(
            f"{host}/api/qt/stock/get?secid={spec.symbol}&ut={UT_TOKEN}"
            "&invt=2&fltt=2&fields=f43,f86"
            for host in QUOTE_HOSTS
        )
        qdata = (json.loads(_http_get(quote_urls, f"{cfg.name}[东财]最新报价"))
                 or {}).get("data") or {}
        price = _positive_float(qdata.get("f43"))
        ts = qdata.get("f86")
        if price is not None and ts:
            quote_price = price
            quote_time = datetime.fromtimestamp(int(ts), ZoneInfo(cfg.timezone))
    except (DataSourceError, ValueError, OSError):
        quote_price, quote_time = None, None  # 报价失败降级为 None，由上层处理

    return AssetData(key=cfg.key, name=cfg.name, bars=bars,
                     quote_price=quote_price, quote_time=quote_time,
                     source=SOURCE_EASTMONEY)


# ---------------------------------------------------------------------------
# 数据源二：腾讯（回退）
# ---------------------------------------------------------------------------

def _fetch_tencent(cfg: AssetConfig, spec: SourceSpec) -> AssetData:
    """腾讯日线 + 实时报价（day 行 [date, open, close, high, low, vol]；
    qt[3]=最新价，qt[30]=时间戳）。"""
    url = (
        f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        f"?param={spec.symbol},day,,,{KLINE_REQUEST_BARS},qfq"
    )
    payload = json.loads(_http_get((url,), f"{cfg.name}[腾讯]历史行情"))
    node = ((payload or {}).get("data") or {}).get(spec.symbol) or {}
    rows = node.get("day")
    if not isinstance(rows, list) or not rows:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}历史行情返回为空。")

    raw_pairs: list[tuple[date, float]] = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 3:
            continue
        try:
            d = date.fromisoformat(str(row[0]).strip())
        except ValueError:
            continue
        raw_pairs.append((d, row[2]))  # 收盘价在第 3 列

    bars = clean_bars(raw_pairs)
    if not bars:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}日线数据全部无效。")

    quote_price: float | None = None
    quote_time: datetime | None = None
    qt = (node.get("qt") or {}).get(spec.symbol) or []
    if len(qt) > 30:
        price = _positive_float(qt[3])
        raw_ts = str(qt[30]).strip()
        if price is not None and raw_ts:
            try:
                # A股格式 20260902143945；美股格式 2026-09-01 17:15:59
                fmt = "%Y-%m-%d %H:%M:%S" if "-" in raw_ts else "%Y%m%d%H%M%S"
                quote_time = datetime.strptime(raw_ts, fmt).replace(
                    tzinfo=ZoneInfo(cfg.timezone)
                )
                quote_price = price
            except ValueError:
                quote_price, quote_time = None, None

    return AssetData(key=cfg.key, name=cfg.name, bars=bars,
                     quote_price=quote_price, quote_time=quote_time,
                     source=SOURCE_TENCENT)


# ---------------------------------------------------------------------------
# 数据源三：新浪财经（黄金现货回退）
# ---------------------------------------------------------------------------

_JSONP_RE = re.compile(r"\((.*)\)\s*;?\s*$", re.S)


def _fetch_sina_gold(cfg: AssetConfig, spec: SourceSpec) -> AssetData:
    """新浪伦敦金：日线历史（JSONP）+ 实时报价（GBK，hf_XAU）。

    实时字段：[0]=最新价，[6]=时间 HH:MM:SS，[12]=日期 YYYY-MM-DD（北京时间）。
    """
    history_url = (
        "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20t=/"
        f"GlobalFuturesService.getGlobalFuturesDailyKLine?symbol={spec.symbol}"
    )
    text = _http_get((history_url,), f"{cfg.name}[新浪]历史行情").decode("utf-8", "replace")
    match = _JSONP_RE.search(text)
    if not match:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}历史行情响应格式异常。")
    rows = json.loads(match.group(1))
    if not isinstance(rows, list) or not rows:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}历史行情返回为空。")

    raw_pairs: list[tuple[date, float]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            d = date.fromisoformat(str(row.get("date", "")).strip())
        except ValueError:
            continue
        raw_pairs.append((d, row.get("close")))

    bars = clean_bars(raw_pairs)
    if not bars:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}日线数据全部无效。")

    quote_price: float | None = None
    quote_time: datetime | None = None
    live_url = f"https://hq.sinajs.cn/list=hf_{spec.symbol}"
    live_text = _http_get((live_url,), f"{cfg.name}[新浪]最新报价",
                          extra_headers=_SINJA_HEADERS).decode("gbk", "replace")
    m = re.search(r'hq_str_\w+="([^"]*)"', live_text)
    if m:
        fields = m.group(1).split(",")
        price = _positive_float(fields[0]) if fields else None
        if price is not None and len(fields) > 12:
            try:
                quote_time = datetime.strptime(
                    f"{fields[12].strip()} {fields[6].strip()}",
                    "%Y-%m-%d %H:%M:%S",
                ).replace(tzinfo=ZoneInfo(cfg.timezone))
                quote_price = price
            except ValueError:
                quote_price, quote_time = None, None

    return AssetData(key=cfg.key, name=cfg.name, bars=bars,
                     quote_price=quote_price, quote_time=quote_time,
                     source=SOURCE_SINA)


# ---------------------------------------------------------------------------
# 数据源四：新浪财经（美股指数回退）
# ---------------------------------------------------------------------------

def _fetch_sina_us(cfg: AssetConfig, spec: SourceSpec) -> AssetData:
    """新浪美股指数：日线历史（US_MinKService.getDailyK，JSONP 数组，键 d/o/h/l/c）
    + 实时报价（hq.sinajs.cn list=gb_<code>，GBK）。

    实时字段：[1]=最新价，[3]=报价时间（新浪服务器均为北京时间，转换为资产时区展示）。
    """
    history_url = (
        "https://stock.finance.sina.com.cn/usstock/api/jsonp.php/var%20t=/"
        f"US_MinKService.getDailyK?symbol={spec.symbol}"
    )
    text = _http_get((history_url,), f"{cfg.name}[新浪]历史行情").decode("utf-8", "replace")
    match = _JSONP_RE.search(text)
    if not match:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}历史行情响应格式异常。")
    rows = json.loads(match.group(1))
    if not isinstance(rows, list) or not rows:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}历史行情返回为空。")

    raw_pairs: list[tuple[date, float]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            d = date.fromisoformat(str(row.get("d", "")).strip())
        except ValueError:
            continue
        raw_pairs.append((d, row.get("c")))

    bars = clean_bars(raw_pairs)
    if not bars:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}日线数据全部无效。")

    quote_price: float | None = None
    quote_time: datetime | None = None
    hq_symbol = "gb_" + spec.symbol.lstrip(".").lower()
    live_url = f"https://hq.sinajs.cn/list={hq_symbol}"
    live_text = _http_get((live_url,), f"{cfg.name}[新浪]最新报价",
                          extra_headers=_SINJA_HEADERS).decode("gbk", "replace")
    m = re.search(r'hq_str_\w+="([^"]*)"', live_text)
    if m:
        fields = m.group(1).split(",")
        price = _positive_float(fields[1]) if len(fields) > 1 else None
        if price is not None and len(fields) > 3:
            try:
                quote_time = (
                    datetime.strptime(fields[3].strip(), "%Y-%m-%d %H:%M:%S")
                    .replace(tzinfo=ZoneInfo("Asia/Shanghai"))
                    .astimezone(ZoneInfo(cfg.timezone))
                )
                quote_price = price
            except ValueError:
                quote_price, quote_time = None, None

    return AssetData(key=cfg.key, name=cfg.name, bars=bars,
                     quote_price=quote_price, quote_time=quote_time,
                     source=SOURCE_SINA)


_FETCHERS = {
    "eastmoney": _fetch_eastmoney,
    "tencent": _fetch_tencent,
    "sina_gold": _fetch_sina_gold,
    "sina_us": _fetch_sina_us,
}


_CACHE_TTL_SECONDS = 60.0  # 真实抓取数据的短时复用窗口（防免费数据源频控），非伪数据
_CACHE: dict[str, tuple[float, AssetData]] = {}
_CACHE_LOCK = threading.Lock()


def fetch_asset_data(cfg: AssetConfig) -> AssetData:
    """带 60 秒短缓存的资产数据获取（缓存的是真实抓取结果，不做任何修改）。

    页面打开/刷新时仍走完整抓取流程；仅当同一资产在 60 秒内被重复请求
    （如浏览器重试、多次刷新）时复用上一次的真实数据，避免触发免费数据源频控。
    """
    now = _monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(cfg.key)
        if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
            return cached[1]
    data = _fetch_from_sources(cfg)
    with _CACHE_LOCK:
        _CACHE[cfg.key] = (_monotonic(), data)
    return data


def _fetch_from_sources(cfg: AssetConfig) -> AssetData:
    """按配置顺序尝试各数据源，返回第一个可用结果。

    - 历史不足 800 根 → 视为该源不可用，继续下一个；
    - 历史 OK 但报价缺失 → 记为降级候选，继续尝试下一个源；
    - 所有源都失败 → 抛出聚合 DataSourceError；
    - 仅剩降级候选时返回之（指数类由 calculator 用最近已完成收盘价兜底）。
    """
    degraded: AssetData | None = None
    tried: list[str] = []
    for spec in cfg.sources:
        fetcher = _FETCHERS.get(spec.kind)
        if fetcher is None:  # 配置错误
            raise DataSourceError(f"当前无法完成计算：{cfg.name}数据源类型未知（{spec.kind}）。")
        try:
            data = fetcher(cfg, spec)
        except MarketDataError:
            continue  # 该源不可用（网络/数据质量），尝试下一个源
        tried.append(data.source)
        if len(data.bars) < HISTORY_DAYS:
            # 历史深度不足 800 根（如腾讯美股指数仅返回最新 1 根）→ 视为该源不可用
            continue
        if data.quote_price is None:
            if degraded is None:
                degraded = data
            continue
        return data
    if degraded is not None:
        return degraded
    raise DataSourceError(
        f"当前无法完成计算：{cfg.name}数据获取失败（已尝试数据源：{'、'.join(tried) or '无'}）。"
    )
