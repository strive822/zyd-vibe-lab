# -*- coding: utf-8 -*-
"""数据层与计算服务单元测试（SMA800 口径、清洗、当前点位兜底）。

核心验收点（需求文档 §19.4 / §19.5）：
  - 每个资产严格使用最近 800 个完整交易日；
  - 当天未收盘的盘中价格不进入 SMA800。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.config import ASSETS
from app.data.market_data import (
    DataQualityError,
    DataSourceError,
    clean_bars,
    select_completed_bars,
)
from app.services.calculator import prepare_asset

CST = ZoneInfo("Asia/Shanghai")

YESTERDAY = date(2026, 9, 1)   # 周二（相对测试用的“今天”）
TODAY = date(2026, 9, 2)       # 周三


def weekday_bars_ending(end_date: date, count: int, base: float = 100.0):
    """生成 count 个连续工作日的 (date, base) 序列，按日期升序，最后一天为 end_date。"""
    bars = []
    d = end_date
    while len(bars) < count:
        if d.weekday() < 5:
            bars.append((d, base))
        d -= timedelta(days=1)
    return tuple(reversed(bars))


def nine_hundred_bars_with_today(today_close: float | None):
    bars = list(weekday_bars_ending(YESTERDAY, 900))
    if today_close is not None:
        bars.append((TODAY, today_close))
    return tuple(bars)


# ---- SMA800 口径 ----

def test_sma_uses_exactly_800_completed_days_and_excludes_intraday():
    """14:00（盘中）：当日K线不进 SMA800；SMA 恰好=800 根已完成交易日均值。"""
    cfg = ASSETS["csi500"]
    bars = nine_hundred_bars_with_today(today_close=999.0)
    now = datetime(2026, 9, 2, 14, 0, tzinfo=CST)  # 15:00 收盘之前
    v = prepare_asset(cfg, bars, quote_price=1100.0,
                      quote_time=now, now=now)
    assert v.sma800 == pytest.approx(100.0)          # 999.0 未被计入
    assert v.ratio == pytest.approx(11.0)            # R = 1100 / 100
    assert v.bars_used == 800                        # 恰好 800 根
    assert v.data_time_text == "2026-09-02 14:00 CST"


def test_after_close_today_bar_enters_sma():
    """15:05（已收盘）：当日K线成为已完成交易日，计入 SMA800。"""
    cfg = ASSETS["csi500"]
    bars = nine_hundred_bars_with_today(today_close=999.0)
    now = datetime(2026, 9, 2, 15, 5, tzinfo=CST)
    v = prepare_asset(cfg, bars, quote_price=999.0, quote_time=now, now=now)
    expected = (799 * 100.0 + 999.0) / 800
    assert v.sma800 == pytest.approx(expected)
    assert v.bars_used == 800


def test_exact_800_bars_pass_and_799_fail():
    """恰好 800 根已完成交易日可计算；799 根必须报“历史数据不足”。"""
    cfg = ASSETS["csi500"]
    now = datetime(2026, 9, 2, 14, 0, tzinfo=CST)
    ok_bars = weekday_bars_ending(YESTERDAY, 800)
    v = prepare_asset(cfg, ok_bars, quote_price=105.0, quote_time=now, now=now)
    assert v.bars_used == 800

    bad_bars = weekday_bars_ending(YESTERDAY, 799)
    with pytest.raises(DataQualityError, match="历史数据不足"):
        prepare_asset(cfg, bad_bars, quote_price=105.0, quote_time=now, now=now)


def test_weekend_no_today_bar():
    """周末：无当日K线，历史全部视为已完成。"""
    cfg = ASSETS["csi500"]
    bars = weekday_bars_ending(date(2026, 9, 4), 900)  # 周五
    now = datetime(2026, 9, 6, 10, 0, tzinfo=CST)      # 周日
    v = prepare_asset(cfg, bars, quote_price=100.0, quote_time=now, now=now)
    assert v.sma800 == pytest.approx(100.0)
    assert v.bars_used == 800


# ---- 当前点位来源 ----

def test_index_quote_missing_falls_back_to_last_completed_close():
    """指数报价缺失：用最近已完成交易日收盘价兜底，时间标注该日收盘时刻。"""
    cfg = ASSETS["csi500"]
    bars = nine_hundred_bars_with_today(today_close=999.0)  # 今日盘中K线存在
    now = datetime(2026, 9, 2, 14, 0, tzinfo=CST)
    v = prepare_asset(cfg, bars, quote_price=None, quote_time=None, now=now)
    assert v.current_price == pytest.approx(100.0)   # 用昨日收盘，绝不用盘中 999
    assert v.data_time_text == "2026-09-01 15:00 CST"


def test_gold_quote_missing_raises():
    """现货黄金无收盘价概念：报价缺失必须报错，不允许编造当前点位。"""
    cfg = ASSETS["gold"]
    bars = weekday_bars_ending(YESTERDAY, 900)
    now = datetime(2026, 9, 2, 14, 0, tzinfo=CST)
    with pytest.raises(DataSourceError, match="最新报价获取失败"):
        prepare_asset(cfg, bars, quote_price=None, quote_time=None, now=now)


@pytest.mark.parametrize("bad_quote", [0.0, -5.0, float("nan"), float("inf")])
def test_invalid_quote_ignored(bad_quote):
    """无效报价（<=0 / NaN / Inf）不得作为当前点位。"""
    cfg = ASSETS["csi500"]
    bars = weekday_bars_ending(YESTERDAY, 900)
    now = datetime(2026, 9, 2, 14, 0, tzinfo=CST)
    v = prepare_asset(cfg, bars, quote_price=bad_quote, quote_time=now, now=now)
    assert v.current_price == pytest.approx(100.0)  # 回退到最近已完成收盘价


# ---- 多源回退链（纯逻辑，mock 掉网络） ----

def _good_asset_data(cfg):
    from app.data import market_data as md

    return md.AssetData(
        key=cfg.key, name=cfg.name,
        bars=weekday_bars_ending(YESTERDAY, 900),
        quote_price=100.0, quote_time=datetime(2026, 9, 2, 14, 0, tzinfo=CST),
        source="腾讯",
    )


def test_fetch_falls_back_to_second_source(monkeypatch):
    """主源抛异常时必须继续尝试回退源，而不是直接失败。"""
    from app.data import market_data as md

    cfg = ASSETS["csi500"]
    good = _good_asset_data(cfg)

    def bad_fetcher(c, s):
        raise md.DataSourceError(f"当前无法完成计算：{c.name}主源失败。")

    def good_fetcher(c, s):
        return good

    monkeypatch.setattr(md, "_CACHE", {})
    monkeypatch.setattr(md, "_FETCHERS",
                        {"eastmoney": bad_fetcher, "tencent": good_fetcher})
    data = md.fetch_asset_data(cfg)
    assert data.source == "腾讯"


def test_fetch_shallow_history_source_is_skipped(monkeypatch):
    """回退源历史不足 800 根时视为不可用（如腾讯美股指数只有 1 根）。"""
    from app.data import market_data as md

    cfg = ASSETS["csi500"]
    shallow = md.AssetData(
        key=cfg.key, name=cfg.name, bars=weekday_bars_ending(YESTERDAY, 1),
        quote_price=100.0, quote_time=datetime(2026, 9, 2, 14, 0, tzinfo=CST),
        source="腾讯",
    )

    def bad_fetcher(c, s):
        raise md.DataSourceError(f"当前无法完成计算：{c.name}主源失败。")

    monkeypatch.setattr(md, "_CACHE", {})
    monkeypatch.setattr(md, "_FETCHERS",
                        {"eastmoney": bad_fetcher, "tencent": lambda c, s: shallow})
    with pytest.raises(md.DataSourceError):
        md.fetch_asset_data(cfg)


def test_fetch_all_sources_fail_raises(monkeypatch):
    """所有源都失败 → 聚合 DataSourceError（绝不返回空/伪数据）。"""
    from app.data import market_data as md

    cfg = ASSETS["csi500"]

    def fail(c, s):
        raise md.DataSourceError(f"当前无法完成计算：{c.name}失败。")

    monkeypatch.setattr(md, "_CACHE", {})
    monkeypatch.setattr(md, "_FETCHERS", {"eastmoney": fail, "tencent": fail})
    with pytest.raises(md.DataSourceError):
        md.fetch_asset_data(cfg)


# ---- 清洗与口径判定 ----

def test_clean_bars_drops_invalid_and_dedupes():
    d1, d2, d3 = date(2026, 8, 28), date(2026, 8, 31), date(2026, 9, 1)
    raw = [
        (d1, 100.0),
        (d1, 101.0),            # 重复日期 → 保留后出现的
        (d2, float("nan")),     # NaN → 丢弃
        (d2, 102.0),
        (d3, -5.0),             # 非正数 → 丢弃
        (d3, float("inf")),     # Infinity → 丢弃
    ]
    assert clean_bars(raw) == ((d1, 101.0), (d2, 102.0))


def test_clean_bars_sorts_ascending():
    d1, d2 = date(2026, 9, 1), date(2026, 8, 31)
    assert clean_bars([(d1, 10.0), (d2, 9.0)]) == ((d2, 9.0), (d1, 10.0))


def test_select_completed_bars_rules():
    cfg = ASSETS["csi500"]
    d_prev, d_today, d_future = date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3)
    bars = ((d_prev, 1.0), (d_today, 2.0), (d_future, 3.0))

    # 盘中 14:00：今日与未来都排除
    now = datetime(2026, 9, 2, 14, 0, tzinfo=CST)
    assert select_completed_bars(bars, now, cfg.close_time) == [(d_prev, 1.0)]

    # 收盘 15:00 整：今日计入（>=）
    now = datetime(2026, 9, 2, 15, 0, tzinfo=CST)
    assert select_completed_bars(bars, now, cfg.close_time) == [(d_prev, 1.0), (d_today, 2.0)]

    # 此后（9-4）回看：三根都是过去的已完成交易日，全部计入
    now = datetime(2026, 9, 4, 20, 0, tzinfo=CST)
    assert select_completed_bars(bars, now, cfg.close_time) == [
        (d_prev, 1.0), (d_today, 2.0), (d_future, 3.0)
    ]

    # 现货黄金（close_time=None）：当日永不计入
    now = datetime(2026, 9, 2, 23, 59, tzinfo=CST)
    assert select_completed_bars(bars, now, ASSETS["gold"].close_time) == [(d_prev, 1.0)]
