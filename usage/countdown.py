"""Presentation-only countdown rules for the M1 example data."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Countdown:
    mode: str
    fields: tuple[tuple[str, str], tuple[str, str], tuple[str, str]]
    status: str

    @property
    def text(self) -> str:
        return "".join(value + unit for value, unit in self.fields)


def present_countdown(recovery_at: datetime | None, now: datetime) -> Countdown | None:
    if recovery_at is None:
        return None
    if recovery_at.tzinfo is None or now.tzinfo is None:
        raise ValueError("recovery_at and now must be timezone-aware")
    seconds = max(0, math.ceil((recovery_at - now).total_seconds()))
    status = "awaiting_confirmation" if seconds == 0 else "active"
    if seconds >= 86400:
        days, tail = divmod(seconds, 86400)
        hours, tail = divmod(tail, 3600)
        minutes = tail // 60
        return Countdown("DHM", ((str(days), "天"), (f"{hours:02d}", "时"), (f"{minutes:02d}", "分")), status)
    hours, tail = divmod(seconds, 3600)
    minutes, seconds = divmod(tail, 60)
    return Countdown("HMS", ((str(hours), "时"), (f"{minutes:02d}", "分"), (f"{seconds:02d}", "秒")), status)
