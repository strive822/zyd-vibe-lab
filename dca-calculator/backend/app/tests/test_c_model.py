# -*- coding: utf-8 -*-
"""C哥模型单元测试（需求文档 §6 / §8）。"""
from __future__ import annotations

import random
import math

import pytest

from app.models.c_model import calculate_c_weights

KEYS = ("ndx", "csi500", "gold")


@pytest.mark.parametrize("ratio", [math.nextafter(0.0, 1.0), 1e-300, 1e300])
def test_equal_extreme_positive_ratios_are_normalized(ratio):
    weights = calculate_c_weights({key: ratio for key in KEYS})
    assert all(math.isfinite(w) and w == pytest.approx(1 / 3) for w in weights.values())


def test_subnormal_ratio_does_not_produce_nan_weights():
    weights = calculate_c_weights({"ndx": math.nextafter(0.0, 1.0), "csi500": 1.0, "gold": 1e300})
    assert all(math.isfinite(w) and w >= 0 for w in weights.values())
    assert sum(weights.values()) == pytest.approx(1.0)


def test_equal_ratios_give_exact_thirds():
    """三个 R 完全相同 → 33.33% / 33.33% / 33.33%。"""
    w = calculate_c_weights({k: 1.0 for k in KEYS})
    for k in KEYS:
        assert w[k] == pytest.approx(1 / 3, abs=1e-12)
    assert sum(w.values()) == pytest.approx(1.0, abs=1e-12)


def test_lower_ratio_gets_higher_weight():
    w = calculate_c_weights({"ndx": 0.8, "csi500": 0.9, "gold": 1.1})
    assert w["ndx"] > w["csi500"] > w["gold"]


def test_weights_sum_to_one_various_inputs():
    rng = random.Random(7)
    for _ in range(300):
        rs = {k: rng.uniform(0.2, 5.0) for k in KEYS}
        w = calculate_c_weights(rs)
        assert sum(w.values()) == pytest.approx(1.0, abs=1e-12)


def test_random_strict_monotonicity():
    """随机大样本：R_A < R_B ⇒ Weight_A > Weight_B（严格）。"""
    rng = random.Random(2026)
    for _ in range(2000):
        rs = {k: rng.uniform(0.3, 3.0) for k in KEYS}
        w = calculate_c_weights(rs)
        order_by_r = sorted(KEYS, key=lambda k: rs[k])
        order_by_w = sorted(KEYS, key=lambda k: w[k], reverse=True)
        assert order_by_r == order_by_w
        if len(set(rs.values())) == 3:
            assert len(set(w.values())) == 3  # 不同 R ⇒ 权重必须严格不同


def test_integer_inputs_accepted():
    w = calculate_c_weights({"ndx": 1, "csi500": 2, "gold": 4})
    assert w["ndx"] > w["csi500"] > w["gold"]


def test_same_input_same_output():
    rs = {"ndx": 0.85, "csi500": 1.02, "gold": 0.97}
    assert calculate_c_weights(rs) == calculate_c_weights(rs)


@pytest.mark.parametrize("bad", [0, -0.5, float("nan"), float("inf"), float("-inf")])
def test_invalid_ratio_raises(bad):
    with pytest.raises(ValueError):
        calculate_c_weights({"a": bad, "b": 1.0, "c": 1.0})
