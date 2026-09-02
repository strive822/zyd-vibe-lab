# -*- coding: utf-8 -*-
"""C哥模型（需求文档 §6，纯函数、无任何可调参数）。

    R_i     = CurrentPrice_i / SMA800_i
    Score_i = 1 / R_i
    Weight_i = Score_i / Σ Score

性质（由公式直接保证，并由单元测试验证）：
  R_A < R_B  ⇒  Weight_A > Weight_B （严格单调）
  三个 R 相同 ⇒ 各 1/3
  权重之和恒为 1，100% 资金始终分配给三个资产。
不使用：平方、波动率、风险参数、权重上下限、现金仓位。
"""
from __future__ import annotations

import math

__all__ = ["calculate_c_weights"]


def _validated_ratios(ratios: dict[str, float]) -> dict[str, float]:
    if not ratios:
        raise ValueError("ratios 不能为空")
    validated: dict[str, float] = {}
    for key, value in ratios.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"R 值必须为数字：{key}={value!r}")
        r = float(value)
        if not math.isfinite(r):
            raise ValueError(f"R 值必须为有限数：{key}={r}")
        if r <= 0:
            raise ValueError(f"R 值必须为正数：{key}={r}")
        validated[key] = r
    return validated


def calculate_c_weights(ratios: dict[str, float]) -> dict[str, float]:
    """C哥模型权重：Score = 1/R，归一化。相同输入恒产生相同输出。"""
    validated = _validated_ratios(ratios)
    scores = {key: 1.0 / r for key, r in validated.items()}
    total = sum(scores.values())
    weights = {key: s / total for key, s in scores.items()}
    # 数值守卫：消除浮点累计误差，保证权重之和精确为 1
    weight_sum = sum(weights.values())
    return {key: w / weight_sum for key, w in weights.items()}
