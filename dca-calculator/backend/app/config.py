# -*- coding: utf-8 -*-
"""全局配置：资产基准、数据源、SMA 口径。

数据源（需求文档 §3 / §18.1，开发前已实际验证，验证脚本见 backend/tools/）：
  主源 = 东方财富（免费、无需 Key），按资产配置回退源：
    - 纳斯达克100 → 东财 secid 100.NDX100（注意：100.NDX 是纳斯达克综合指数，勿用）
                    回退：腾讯 usNDX
    - 中证500     → 东财 secid 1.000905
                    回退：腾讯 sh000905
    - 黄金/美元现货 → 东财 secid 122.XAU（SecurityType=现货）
                    回退：新浪财经 hf_XAU（伦敦金/现货黄金）

  东财端点回退（本机实测 HTTPS 主域不稳定，HTTP 与数字子域镜像可用）。
  本机实测东财 WAF 会按 TLS/请求头指纹拦截脚本客户端（RemoteDisconnected），
  必须携带浏览器级请求头并使用 Connection: close。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time

# ---- 口径 ----
HISTORY_DAYS = 800          # SMA800：恰好 800 个已完成交易日
KLINE_REQUEST_BARS = 2000   # 单次请求根数上限（远大于 800，保证窗口充足）
HTTP_TIMEOUT = 15           # 单次请求超时（秒）
# 请求策略：每个 URL 先直连（绕过系统代理）再走系统代理，见 market_data._http_get

# ---- 通用请求头（浏览器级，绕过东财 WAF 指纹拦截）----
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "close",
}

# ---- 数据源端点 ----
UT_TOKEN = "fa5fd1943c7b386f172d6893dbfba10b"  # 东财网页端公共令牌（公开固定值，非密钥）
KLINE_HOSTS = (
    "http://push2his.eastmoney.com",
    "https://92.push2his.eastmoney.com",
)
QUOTE_HOSTS = (
    "http://push2.eastmoney.com",
    "https://82.push2.eastmoney.com",
)


@dataclass(frozen=True)
class SourceSpec:
    """单个数据源定义。kind 决定解析器；symbol 为该源的代码。"""

    kind: str    # "eastmoney" | "tencent" | "sina_gold"
    symbol: str


@dataclass(frozen=True)
class AssetConfig:
    key: str
    name: str
    timezone: str            # 判定“今天/收盘”所用时区
    close_time: time | None  # None = 现货无收盘概念（当日K线永不计入 SMA）
    tz_label: str            # 页面展示用时区标签
    sources: tuple[SourceSpec, ...]  # 按序尝试，主源在前


ASSETS: dict[str, AssetConfig] = {
    "ndx": AssetConfig(
        key="ndx", name="纳斯达克100",
        timezone="America/New_York", close_time=time(16, 0), tz_label="ET",
        sources=(
            SourceSpec("eastmoney", "100.NDX100"),
            # 腾讯 usNDX 仅返回最新 1 根日线（实测无深历史），不采用
            SourceSpec("sina_us", ".NDX"),
        ),
    ),
    "csi500": AssetConfig(
        key="csi500", name="中证500",
        timezone="Asia/Shanghai", close_time=time(15, 0), tz_label="CST",
        sources=(
            SourceSpec("eastmoney", "1.000905"),
            SourceSpec("tencent", "sh000905"),
        ),
    ),
    "gold": AssetConfig(
        key="gold", name="黄金",
        timezone="Asia/Shanghai", close_time=None, tz_label="UTC+8",
        sources=(
            SourceSpec("eastmoney", "122.XAU"),
            SourceSpec("sina_gold", "XAU"),
        ),
    ),
}

ASSET_ORDER: tuple[str, ...] = ("ndx", "csi500", "gold")
