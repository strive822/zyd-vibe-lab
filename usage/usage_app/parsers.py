"""Defensive parsers: only documented or explicitly verified source semantics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import cast

from .models import Account, Balance, ErrorCode, Provider, ProviderError, QuotaWindow, RecoveryKind, UsageSnapshot


def object_map(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    return cast(dict[str, object], value)


def items(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    return cast(list[object], value)


def number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    return float(value)


def percentage(value: object) -> float:
    result = number(value)
    if not 0 <= result <= 100:
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    return result


def integer(value: object) -> int:
    result = number(value)
    if result != int(result):
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    return int(result)


def money(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise ProviderError(ErrorCode.INCOMPATIBLE) from None
    if not result.is_finite() or result < 0:
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    return result


def timestamp(value: object, *, milliseconds: bool = False) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(number(value) / (1000 if milliseconds else 1), UTC)
    except (ValueError, OverflowError, OSError):
        raise ProviderError(ErrorCode.INCOMPATIBLE) from None


def require_provider(account: Account, provider: Provider) -> None:
    if account.provider != provider:
        raise ValueError("Adapter/account mismatch")


def parse_codex(raw: object, account: Account, now: datetime) -> UsageSnapshot:
    require_provider(account, Provider.CODEX)
    body = object_map(raw)
    if "rateLimits" not in body and "rateLimitsByLimitId" not in body:
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    by_id = body.get("rateLimitsByLimitId")
    if by_id is not None:
        buckets = object_map(by_id)
    elif body.get("rateLimits") is not None:
        single = object_map(body["rateLimits"])
        bucket_id = single.get("limitId")
        buckets = {bucket_id if isinstance(bucket_id, str) else "default": single}
    else:
        buckets = {}
    windows = []
    for bucket_id, raw_bucket in buckets.items():
        bucket = object_map(raw_bucket)
        for position in ("primary", "secondary"):
            if bucket.get(position) is None:
                continue
            entry = object_map(bucket[position])
            duration = integer(entry["windowDurationMins"]) if entry.get("windowDurationMins") is not None else None
            remaining = 100 - percentage(entry["usedPercent"]) if entry.get("usedPercent") is not None else None
            recovery = timestamp(entry.get("resetsAt"))
            try:
                windows.append(QuotaWindow(f"{bucket_id}:{position}", bucket_id, duration, remaining,
                                           RecoveryKind.FIXED_RESET if recovery else RecoveryKind.UNKNOWN,
                                           recovery, label=position))
            except ValueError:
                raise ProviderError(ErrorCode.INCOMPATIBLE) from None
    return UsageSnapshot(account.id, account.provider, "codex-app-server", tuple(windows), (), now)


def parse_deepseek(raw: object, account: Account, now: datetime) -> UsageSnapshot:
    require_provider(account, Provider.DEEPSEEK)
    body = object_map(raw)
    available = body.get("is_available")
    if not isinstance(available, bool):
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    balances = []
    currencies = set()
    for value in items(body.get("balance_infos")):
        entry = object_map(value)
        currency = entry.get("currency")
        if not isinstance(currency, str) or currency in currencies or not currency or len(currency) > 8:
            raise ProviderError(ErrorCode.INCOMPATIBLE)
        currencies.add(currency)
        balances.append(Balance(currency, money(entry.get("total_balance")),
                                money(entry["granted_balance"]) if entry.get("granted_balance") is not None else None,
                                money(entry["topped_up_balance"]) if entry.get("topped_up_balance") is not None else None,
                                available))
    return UsageSnapshot(account.id, account.provider, "deepseek-balance", (), tuple(balances), now)


@dataclass(frozen=True, slots=True)
class GlmWindowMapping:
    """An explicit source identity whose semantics have primary-source evidence."""

    source_type: str
    duration_minutes: int
    percentage_is_used: bool
    recovery_field: str | None = None
    recovery_milliseconds: bool = False
    recovery_kind: RecoveryKind = RecoveryKind.UNKNOWN
    source_unit: int | None = None
    source_number: int | None = None

    def matches(self, entry: dict[str, object]) -> bool:
        return (entry.get("type") == self.source_type
                and (self.source_unit is None or type(entry.get("unit")) is int and entry["unit"] == self.source_unit)
                and (self.source_number is None or type(entry.get("number")) is int and entry["number"] == self.source_number))


# Official personal usage page: CREDIT_LIMIT/unit=3 is 5h, unit=6 is weekly;
# the displayed percentage is explicitly labelled used. The actual account
# response also confirms number=5/1 and a Unix-millisecond weekly reset.
GLM_PERSONAL_MAPPING = (
    GlmWindowMapping("CREDIT_LIMIT", 300, True, "nextResetTime", True, RecoveryKind.ROLLING, 3, 5),
    GlmWindowMapping("CREDIT_LIMIT", 10080, True, "nextResetTime", True, RecoveryKind.FIXED_RESET, 6, 1),
)


def parse_glm(raw: object, account: Account, now: datetime,
              verified_mapping: tuple[GlmWindowMapping, ...] = ()) -> UsageSnapshot:
    require_provider(account, Provider.GLM)
    body = object_map(raw)
    # The legacy official plugin's type-only TOKENS=5h assumption is unsafe.
    # Match the complete verified identity instead of response order or total.
    data = object_map(body.get("data"))
    limits = items(data.get("limits"))
    if not verified_mapping:
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    windows = []
    seen = set()
    for value in limits:
        entry = object_map(value)
        kind = entry.get("type")
        if not isinstance(kind, str):
            raise ProviderError(ErrorCode.INCOMPATIBLE)
        rules = [rule for rule in verified_mapping if rule.matches(entry)]
        if not rules:
            continue  # Unknown/MCP/monthly rows do not become model quotas.
        if len(rules) != 1:
            raise ProviderError(ErrorCode.INCOMPATIBLE)
        rule = rules[0]
        identity = (rule.source_type, rule.source_unit, rule.source_number)
        if identity in seen:
            raise ProviderError(ErrorCode.INCOMPATIBLE)
        seen.add(identity)
        raw_percent = entry.get("percentage")
        proportion = percentage(raw_percent) if raw_percent is not None else None
        if proportion is not None and rule.percentage_is_used:
            proportion = 100 - proportion
        recovery = timestamp(entry.get(rule.recovery_field), milliseconds=rule.recovery_milliseconds) if rule.recovery_field else None
        try:
            window_id = kind if rule.source_unit is None else f"{kind}:{rule.source_unit}:{rule.source_number}"
            windows.append(QuotaWindow(window_id, kind, rule.duration_minutes, proportion,
                                       rule.recovery_kind if recovery else RecoveryKind.UNKNOWN, recovery))
        except ValueError:
            raise ProviderError(ErrorCode.INCOMPATIBLE) from None
    if limits and not windows:
        raise ProviderError(ErrorCode.INCOMPATIBLE)
    return UsageSnapshot(account.id, account.provider, "glm-personal-plan", tuple(windows), (), now)
