# -*- coding: utf-8 -*-
"""严谨模型（需求文档 §7，与 C哥模型完全独立，纯函数）。

    V_i      = -ln(R_i)
    Score_i  = exp(sign(V_i) × |V_i|^γ)，γ = 1.5 固定，不提供用户设置
    Weight_i = Score_i / Σ Score

性质（由公式直接保证，并由单元测试验证）：
  R 越低 ⇒ V 越高 ⇒ Score 越高 ⇒ Weight 越高（严格单调，
  即使 R_A = 0.800、R_B = 0.801，A 的权重也必须严格高于 B）。
  三个 R 相同 ⇒ 各 1/3；权重之和恒为 1；全部 R > 1 时资金仍 100% 分配。
不使用：波动率修正、最高/最低权重、风险偏好、参数滑块、现金仓位。
"""
from __future__ import annotations

import math

from app.models.c_model import _validated_ratios

__all__ = ["GAMMA", "calculate_rigorous_weights", "rigorous_score"]

GAMMA = 1.5  # 固定指数，禁止暴露为配置


def rigorous_score(r: float) -> float:
    """单个资产的 Score = exp(sign(V) · |V|^γ)，V = -ln(r)。"""
    v = -math.log(r)
    return math.exp(math.copysign(abs(v) ** GAMMA, v))


def calculate_rigorous_weights(ratios: dict[str, float]) -> dict[str, float]:
    """严谨模型权重。相同输入恒产生相同输出。"""
    validated = _validated_ratios(ratios)
    scores = {key: rigorous_score(r) for key, r in validated.items()}
    total = sum(scores.values())
    weights = {key: s / total for key, s in scores.items()}
    # 数值守卫：消除浮点累计误差，保证权重之和精确为 1
    weight_sum = sum(weights.values())
    return {key: w / weight_sum for key, w in weights.items()}
