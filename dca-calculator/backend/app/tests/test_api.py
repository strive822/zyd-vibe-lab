# -*- coding: utf-8 -*-
"""API 层测试：错误语义（需求文档 §15 / §19.14）——数据失败时明确报错，绝不输出错误权重。"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.data.market_data import DataQualityError, DataSourceError
from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_data_quality_error_returns_502_with_message(monkeypatch):
    """历史数据不足 → 502 + 明确中文报错（响应中没有任何权重字段）。"""

    def boom(now_provider=None):
        raise DataQualityError(
            "当前无法完成计算：中证500历史数据不足（有效完整交易日 12 根，需要 800 根）。"
        )

    monkeypatch.setattr("app.main.run_calculation", boom)
    resp = client.get("/api/calculation")
    assert resp.status_code == 502
    assert "当前无法完成计算" in resp.json()["detail"]
    assert "c_model" not in resp.json()


def test_source_error_returns_502_with_message(monkeypatch):
    """数据源失败 → 502 + 明确中文报错。"""

    def boom(now_provider=None):
        raise DataSourceError("当前无法完成计算：黄金最新报价获取失败（网络异常）。")

    monkeypatch.setattr("app.main.run_calculation", boom)
    resp = client.get("/api/calculation")
    assert resp.status_code == 502
    assert "当前无法完成计算" in resp.json()["detail"]


def test_success_shape(monkeypatch):
    """正常路径：响应含两模型权重（和为 1）与三资产行情时间。"""

    def fake(now_provider=None):
        return {
            "c_model": {"ndx": 0.5, "csi500": 0.3, "gold": 0.2},
            "rigorous_model": {"ndx": 0.4, "csi500": 0.35, "gold": 0.25},
            "assets": [
                {"key": "ndx", "name": "纳斯达克100", "data_time": "2026-09-01 16:00 ET", "source": "东方财富"},
                {"key": "csi500", "name": "中证500", "data_time": "2026-09-02 14:55 CST", "source": "东方财富"},
                {"key": "gold", "name": "黄金", "data_time": "2026-09-02 15:02 UTC+8", "source": "东方财富"},
            ],
        }

    monkeypatch.setattr("app.main.run_calculation", fake)
    resp = client.get("/api/calculation")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"c_model", "rigorous_model", "assets"}
    assert len(body["assets"]) == 3
    assert all("data_time" in a for a in body["assets"])
    # 响应中不允许出现 CurrentPrice / SMA800 / R / Score
    assert "ratio" not in str(body).lower()
