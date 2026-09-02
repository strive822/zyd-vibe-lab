# -*- coding: utf-8 -*-
"""API 响应模型（Pydantic）。不暴露 CurrentPrice / SMA800 / R / Score。"""
from __future__ import annotations

from pydantic import BaseModel


class AssetInfo(BaseModel):
    key: str
    name: str
    data_time: str  # 该资产实际参与计算的行情时间，如 "2026-09-02 14:55 CST"
    source: str


class CalculationResponse(BaseModel):
    c_model: dict[str, float]        # key → 权重（完整浮点精度，和 = 1）
    rigorous_model: dict[str, float]
    assets: list[AssetInfo]
