"""Versioned ordinary benefit rules. Promotions are deliberately not loaded."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum
from zoneinfo import ZoneInfo

from .models import Provider, aware


class BenefitStatus(StrEnum):
    STANDARD = "standard"
    DISCOUNT = "discount"
    UNVERIFIED = "unverified"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class HolidayCalendar:
    year: int
    dates: frozenset[date]
    source_url: str
    verified_at: date
    complete: bool = True


@dataclass(frozen=True, slots=True)
class BenefitRule:
    id: str
    provider: Provider
    version: str
    timezone: str
    effective_from: date
    effective_to: date | None
    model_scope: tuple[str, ...]
    peak_intervals: tuple[tuple[time, time], ...]
    exclude_holidays: bool
    benefit_kind: str
    factor: Decimal
    source_url: str
    verified_at: date


@dataclass(frozen=True, slots=True)
class BenefitResult:
    status: BenefitStatus
    kind: str
    factor: Decimal | None
    next_transition_at: datetime | None
    rule: BenefitRule


def _range(start: str, end: str) -> set[date]:
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    return {first + timedelta(days=offset) for offset in range((last - first).days + 1)}


CALENDAR_2026 = HolidayCalendar(2026, frozenset().union(
    _range("2026-01-01", "2026-01-03"), _range("2026-02-15", "2026-02-23"),
    _range("2026-04-04", "2026-04-06"), _range("2026-05-01", "2026-05-05"),
    _range("2026-06-19", "2026-06-21"), _range("2026-09-25", "2026-09-27"),
    _range("2026-10-01", "2026-10-07")),
    "https://www.gov.cn/zhengce/zhengceku/202511/content_7047091.htm", date(2026, 9, 30))

RULES = {
    Provider.GLM: BenefitRule("glm-ordinary", Provider.GLM, "2026-09-30", "Asia/Shanghai", date(2026, 9, 27), None,
        ("GLM-5.3", "GLM-5.3-Flash"), ((time(14), time(18)),), False, "model_credit_multiplier", Decimal("0.5"),
        "https://docs.bigmodel.cn/cn/coding-plan/overview", date(2026, 9, 30)),
    Provider.DEEPSEEK: BenefitRule("deepseek-ordinary", Provider.DEEPSEEK, "2026-09-30", "Asia/Shanghai", date(2026, 9, 27), None,
        ("deepseek-flash", "deepseek-v4-pro"), ((time(9), time(12)), (time(14), time(18))), True, "price_multiplier", Decimal("0.5"),
        "https://api-docs.deepseek.com/zh-cn/quick_start/pricing/", date(2026, 9, 30)),
}


class RuleEngine:
    def __init__(self, calendars: tuple[HolidayCalendar, ...] = (CALENDAR_2026,)) -> None:
        self.calendars = {calendar.year: calendar for calendar in calendars}

    def _status(self, local: datetime, rule: BenefitRule) -> BenefitStatus:
        today = local.date()
        if today < rule.effective_from or (rule.effective_to and today > rule.effective_to):
            return BenefitStatus.UNVERIFIED
        in_peak = local.weekday() < 5 and any(start <= local.time() < end for start, end in rule.peak_intervals)
        if not in_peak:
            return BenefitStatus.DISCOUNT  # Missing calendar cannot affect a weekend or night.
        if rule.exclude_holidays:
            calendar = self.calendars.get(today.year)
            if calendar is None or not calendar.complete:
                return BenefitStatus.UNVERIFIED
            if today in calendar.dates:
                return BenefitStatus.DISCOUNT
        return BenefitStatus.STANDARD

    def evaluate(self, now: datetime, rule: BenefitRule, *, model: str | None = None) -> BenefitResult:
        aware(now)
        if model is not None and model not in rule.model_scope:
            return BenefitResult(BenefitStatus.NOT_APPLICABLE, rule.benefit_kind, None, None, rule)
        local = now.astimezone(ZoneInfo(rule.timezone))
        status = self._status(local, rule)
        candidates = []
        for offset in range(10):
            day = local.date() + timedelta(days=offset)
            for boundary in (time(0), *(item for span in rule.peak_intervals for item in span)):
                when = datetime.combine(day, boundary, local.tzinfo)
                if when > local and self._status(when, rule) != status:
                    candidates.append(when.astimezone(UTC))
        next_at = min(candidates) if candidates else None
        factor = rule.factor if status == BenefitStatus.DISCOUNT else Decimal(1) if status == BenefitStatus.STANDARD else None
        return BenefitResult(status, rule.benefit_kind, factor, next_at, rule)
