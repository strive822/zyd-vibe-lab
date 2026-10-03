"""Malformed provider replies must not bypass the configured fallback source."""
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.config import ASSETS
from app.data import market_data


@pytest.mark.parametrize("payload", [b"not JSON", b"[]", b'{"data": [1]}'])
def test_malformed_primary_reply_uses_the_next_source(payload, monkeypatch):
    cfg = ASSETS["csi500"]
    calls = []
    fallback = market_data.AssetData(
        cfg.key, cfg.name,
        tuple((date(2020, 1, 1) + timedelta(days=i), 100.0) for i in range(800)),
        100.0, datetime(2026, 10, 3, tzinfo=ZoneInfo(cfg.timezone)), "SYNTHETIC TEST ONLY",
    )
    monkeypatch.setattr(market_data, "_http_get", lambda *args, **kwargs: payload)

    def next_source(*args):
        calls.append("fallback")
        return fallback

    monkeypatch.setitem(market_data._FETCHERS, "tencent", next_source)
    assert market_data._fetch_from_sources(cfg) is fallback
    assert calls == ["fallback"]


def test_every_malformed_source_returns_a_data_error(monkeypatch):
    def malformed(*args):
        raise json.JSONDecodeError("SYNTHETIC malformed response", "", 0)

    monkeypatch.setitem(market_data._FETCHERS, "eastmoney", malformed)
    monkeypatch.setitem(market_data._FETCHERS, "tencent", malformed)
    with pytest.raises(market_data.DataSourceError, match="东方财富、腾讯"):
        market_data._fetch_from_sources(ASSETS["csi500"])
