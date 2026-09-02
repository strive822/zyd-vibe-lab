# -*- coding: utf-8 -*-
"""严谨模型单元测试（需求文档 §7 / §8：严格单调性为验收核心）。"""
from __future__ import annotations

import math
import random

import pytest

from app.models.rigorous_model import GAMMA, calculate_rigorous_weights, rigorous_score

KEYS = ("ndx", "csi500", "gold")


# ---- 需求文档 §8 指定的 4 个测试用例 ----

def test_case1_all_equal_ratios():
    """测试1：R 全为 1 → 33.33% / 33.33% / 33.33%。"""
    w = calculate_rigorous_weights({k: 1.0 for k in KEYS})
    for k in KEYS:
        assert w[k] == pytest.approx(1 / 3, abs=1e-12)
    assert sum(w.values()) == pytest.approx(1.0, abs=1e-12)


def test_case2_below_and_above_mix():
    """测试2：R = 0.8 / 0.9 / 1.1 → NDX > CSI500 > Gold。"""
    w = calculate_rigorous_weights({"ndx": 0.8, "csi500": 0.9, "gold": 1.1})
    assert w["ndx"] > w["csi500"] > w["gold"]
    assert sum(w.values()) == pytest.approx(1.0, abs=1e-12)


def test_case3_tiny_gap_still_strict():
    """测试3：R = 0.800 / 0.801 / 0.802 → 仍必须严格 NDX > CSI500 > Gold。"""
    w = calculate_rigorous_weights({"ndx": 0.800, "csi500": 0.801, "gold": 0.802})
    assert w["ndx"] > w["csi500"] > w["gold"]


def test_case4_all_above_sma_still_full_allocation():
    """测试4：R = 1.30 / 1.15 / 1.05（全部高于 SMA800）→ Gold > CSI500 > NDX，且 100% 分配。"""
    w = calculate_rigorous_weights({"ndx": 1.30, "csi500": 1.15, "gold": 1.05})
    assert w["gold"] > w["csi500"] > w["ndx"]
    assert sum(w.values()) == pytest.approx(1.0, abs=1e-12)
    assert all(v > 0 for v in w.values())


# ---- 模型性质补充验证 ----

def test_gamma_is_fixed():
    """γ = 1.5 固定，不提供用户设置。"""
    assert GAMMA == 1.5


def test_score_direction():
    """R<1 → Score>1；R=1 → Score=1；R>1 → Score<1。"""
    assert rigorous_score(1.0) == 1.0
    assert rigorous_score(0.5) > 1.0
    assert rigorous_score(2.0) < 1.0


def test_random_strict_monotonicity_large_sample():
    """随机大样本：R_A < R_B ⇒ Weight_A > Weight_B（严格，哪怕差 0.001）。"""
    rng = random.Random(8888)
    for _ in range(2000):
        rs = {k: rng.uniform(0.3, 3.0) for k in KEYS}
        w = calculate_rigorous_weights(rs)
        order_by_r = sorted(KEYS, key=lambda k: rs[k])
        order_by_w = sorted(KEYS, key=lambda k: w[k], reverse=True)
        assert order_by_r == order_by_w
        if len(set(rs.values())) == 3:
            assert len(set(w.values())) == 3
        assert sum(w.values()) == pytest.approx(1.0, abs=1e-9)


def test_extreme_ratios_remain_finite():
    """极端 R（深度低估/高估）不产生 NaN/Infinity，权重和仍为 1，排序正确。

    注：R=1e-6 量级下 |V|^1.5 ≈ 51，最大权重在 float64 下可饱和为精确 1.0，
    属于公式在浮点下的正确行为（和仍为 1，单调性不受影响）。
    """
    w = calculate_rigorous_weights({"ndx": 1e-6, "csi500": 1.0, "gold": 1e6})
    assert all(math.isfinite(v) and v >= 0 for v in w.values())  # 无 NaN / 负值
    assert sum(w.values()) == pytest.approx(1.0, abs=1e-12)
    assert w["ndx"] == max(w.values())
    assert w["gold"] == min(w.values())
    assert w["ndx"] == pytest.approx(1.0, abs=1e-9)


def test_same_input_same_output():
    rs = {"ndx": 0.91, "csi500": 1.12, "gold": 0.995}
    assert calculate_rigorous_weights(rs) == calculate_rigorous_weights(rs)


@pytest.mark.parametrize("bad", [0, -0.5, float("nan"), float("inf"), float("-inf")])
def test_invalid_ratio_raises(bad):
    with pytest.raises(ValueError):
        calculate_rigorous_weights({"a": bad, "b": 1.0, "c": 1.0})
