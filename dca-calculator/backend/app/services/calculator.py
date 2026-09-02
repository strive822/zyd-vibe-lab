# -*- coding: utf-8 -*-
"""计算服务：行情 → SMA800 → R → 两套独立模型 → 权重。

流程（需求文档 §12，仅在打开/刷新页面时执行一次）：
  获取最新行情 → 获取历史日线 → 筛选最近 800 个已完成交易日
  → 计算 SMA800 → 计算 R → 分别运行 C哥模型 / 严谨模型 → 返回权重

精度约定（需求文档 §16）：
  - R / Score / Weight 全程保持完整浮点精度，不过早四舍五入；
  - 内部三个权重之和必须 = 1（模型内部已做归一化守卫）。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.config import ASSETS, ASSET_ORDER, HISTORY_DAYS, AssetConfig
from app.data.market_data import (
    DataQualityError,
    DataSourceError,
    MarketDataError,
    fetch_asset_data,
    format_price_time,
    select_completed_bars,
)
from app.models.c_model import calculate_c_weights
from app.models.rigorous_model import calculate_rigorous_weights


@dataclass(frozen=True)
class AssetValuation:
    config: AssetConfig
    current_price: float   # 当前最新有效点位
    sma800: float          # 恰好 800 个已完成交易日收盘均价
    ratio: float           # R = current_price / sma800
    data_time_text: str    # 展示用行情时间，如 "2026-09-01 16:00 ET"
    bars_used: int
    source: str            # 实际使用的数据源


def prepare_asset(
    cfg: AssetConfig,
    bars: tuple[tuple[date, float], ...],
    quote_price: float | None,
    quote_time: datetime | None,
    now: datetime,
    source: str = "东方财富",
) -> AssetValuation:
    """单个资产的估值（纯函数，可单测；不触网）。"""
    completed = select_completed_bars(bars, now, cfg.close_time)
    if len(completed) < HISTORY_DAYS:
        raise DataQualityError(
            f"当前无法完成计算：{cfg.name}历史数据不足"
            f"（有效完整交易日 {len(completed)} 根，需要 {HISTORY_DAYS} 根）。"
        )
    window = completed[-HISTORY_DAYS:]  # 恰好最近 800 个已完成交易日
    sma800 = sum(c for _, c in window) / HISTORY_DAYS
    if not math.isfinite(sma800) or sma800 <= 0:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}的 SMA800 无效。")

    # 当前点位：优先最新报价；报价缺失/无效时仅指数类可用“最近已完成交易日收盘价”兜底
    quote_ok = (
        quote_price is not None
        and quote_time is not None
        and math.isfinite(quote_price)
        and quote_price > 0
    )
    if quote_ok:
        current_price = float(quote_price)
        price_time = quote_time  # 已验证非空（与 quote_price 同时返回）
    else:
        if cfg.close_time is None:
            # 现货黄金无“收盘价”概念，报价拿不到就不能编造当前点位
            raise DataSourceError(f"当前无法完成计算：{cfg.name}最新报价获取失败。")
        last_date, last_close = completed[-1]
        current_price = last_close
        price_time = datetime.combine(
            last_date, cfg.close_time, tzinfo=ZoneInfo(cfg.timezone)
        )
    if not math.isfinite(current_price) or current_price <= 0:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}当前点位无效。")

    ratio = current_price / sma800
    if not math.isfinite(ratio) or ratio <= 0:
        raise DataQualityError(f"当前无法完成计算：{cfg.name}估值比率无效。")

    return AssetValuation(
        config=cfg,
        current_price=current_price,
        sma800=sma800,
        ratio=ratio,
        data_time_text=format_price_time(price_time, cfg),
        bars_used=len(window),
        source=source,
    )


def run_calculation(now_provider=None) -> dict:
    """完整计算流程。任何一个资产失败都会抛 MarketDataError（绝不返回错误权重）。

    整流重试：免费数据源存在秒级瞬断，首次失败后等待 2 秒整体重试一次；
    两次都失败才向上抛错（配合 60 秒真实数据缓存，正常情况下极少触发）。

    now_provider: 测试注入用，签名 (tz: ZoneInfo) -> datetime；生产传 None。
    """
    last_error: MarketDataError | None = None
    for attempt in range(2):
        try:
            return _run_once(now_provider)
        except MarketDataError as exc:
            last_error = exc
            if attempt == 0:
                _wait(2.0)
    assert last_error is not None
    raise last_error


def _wait(seconds: float) -> None:
    from time import sleep

    sleep(seconds)


def _run_once(now_provider=None) -> dict:
    valuations: dict[str, AssetValuation] = {}
    for key in ASSET_ORDER:
        cfg = ASSETS[key]
        data = fetch_asset_data(cfg)
        tz = ZoneInfo(cfg.timezone)
        now = now_provider(tz) if now_provider is not None else datetime.now(tz)
        valuations[key] = prepare_asset(
            cfg, data.bars, data.quote_price, data.quote_time, now,
            source=data.source,
        )

    ratios = {key: valuations[key].ratio for key in ASSET_ORDER}
    weights_c = calculate_c_weights(ratios)
    weights_rigorous = calculate_rigorous_weights(ratios)

    return {
        "c_model": weights_c,
        "rigorous_model": weights_rigorous,
        "assets": [
            {
                "key": key,
                "name": valuations[key].config.name,
                "data_time": valuations[key].data_time_text,
                "source": valuations[key].source,
            }
            for key in ASSET_ORDER
        ],
    }
