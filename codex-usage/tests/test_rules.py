from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from usage_app.models import Provider
from usage_app.rules import BenefitStatus, RULES, RuleEngine


@pytest.mark.parametrize("provider,wall,expected", [
    (Provider.GLM, "2026-09-30T13:59:59", BenefitStatus.DISCOUNT),
    (Provider.GLM, "2026-09-30T14:00:00", BenefitStatus.STANDARD),
    (Provider.GLM, "2026-09-30T18:00:00", BenefitStatus.DISCOUNT),
    # Ordinary GLM rule has no holiday override; temporary campaign not loaded.
    (Provider.GLM, "2026-10-01T15:00:00", BenefitStatus.STANDARD),
    (Provider.DEEPSEEK, "2026-09-30T09:00:00", BenefitStatus.STANDARD),
    (Provider.DEEPSEEK, "2026-09-30T12:00:00", BenefitStatus.DISCOUNT),
    (Provider.DEEPSEEK, "2026-09-30T14:00:00", BenefitStatus.STANDARD),
    (Provider.DEEPSEEK, "2026-09-30T18:00:00", BenefitStatus.DISCOUNT),
    (Provider.DEEPSEEK, "2026-10-01T09:00:00", BenefitStatus.DISCOUNT),
    # Makeup Saturday remains Saturday; not silently a billing weekday.
    (Provider.DEEPSEEK, "2026-10-10T09:00:00", BenefitStatus.DISCOUNT),
])
def test_rule_boundaries(provider, wall, expected):
    now = datetime.fromisoformat(wall).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    engine = RuleEngine()
    result = engine.evaluate(now, RULES[provider])
    assert result.status == expected
    assert engine.evaluate(now.astimezone(ZoneInfo("America/New_York")), RULES[provider]) == result
    assert result.factor == (Decimal("0.5") if expected == BenefitStatus.DISCOUNT else Decimal(1))


def test_missing_calendar_only_blocks_affected_peak_interval():
    engine = RuleEngine(calendars=())
    rule = RULES[Provider.DEEPSEEK]
    at = datetime(2026, 10, 1, 10, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert engine.evaluate(at, rule).status == BenefitStatus.UNVERIFIED
    assert engine.evaluate(at.replace(hour=19), rule).status == BenefitStatus.DISCOUNT
    assert engine.evaluate(at.replace(year=2027), rule).status == BenefitStatus.UNVERIFIED


def test_transition_skips_unchanged_boundaries_and_scope_is_explicit():
    engine = RuleEngine()
    at = datetime(2026, 9, 30, 8, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert engine.evaluate(at, RULES[Provider.DEEPSEEK]).next_transition_at.astimezone(at.tzinfo).hour == 9
    assert engine.evaluate(at, RULES[Provider.GLM]).next_transition_at.astimezone(at.tzinfo).hour == 14
    assert engine.evaluate(at, RULES[Provider.GLM], model="MCP-tools").status == BenefitStatus.NOT_APPLICABLE
    with pytest.raises(ValueError):
        engine.evaluate(at.replace(tzinfo=None), RULES[Provider.GLM])
