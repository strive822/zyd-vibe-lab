"""Provider-neutral contracts. Secrets and UI objects do not enter these models."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class Provider(StrEnum):
    CODEX = "codex"
    GLM = "glm"
    DEEPSEEK = "deepseek"


class Status(StrEnum):
    DISCONNECTED = "disconnected"
    LOADING = "loading"
    FRESH = "fresh"
    STALE = "stale"
    OFFLINE = "offline"
    AUTH_REQUIRED = "auth_required"
    RATE_LIMITED = "rate_limited"
    INCOMPATIBLE = "incompatible"


class ErrorCode(StrEnum):
    UNCONFIGURED = "unconfigured"
    AUTH_REQUIRED = "auth_required"
    FORBIDDEN = "forbidden"
    NETWORK = "network"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    SERVICE = "service"
    INCOMPATIBLE = "incompatible"
    CANCELLED = "cancelled"


ERROR_MESSAGES = {
    ErrorCode.UNCONFIGURED: "尚未连接",
    ErrorCode.AUTH_REQUIRED: "请重新授权",
    ErrorCode.FORBIDDEN: "此账户没有读取权限",
    ErrorCode.NETWORK: "暂时无法连接",
    ErrorCode.TIMEOUT: "读取超时",
    ErrorCode.RATE_LIMITED: "等待平台冷却",
    ErrorCode.SERVICE: "平台暂时不可用",
    ErrorCode.INCOMPATIBLE: "响应字段待核验",
    ErrorCode.CANCELLED: "读取已取消",
}


class ProviderError(Exception):
    """A classified error; raw provider bodies and keys are never retained."""

    def __init__(self, code: ErrorCode, retry_after: float | None = None):
        self.code = code
        self.retry_after = retry_after
        super().__init__(ERROR_MESSAGES[code])


class RecoveryKind(StrEnum):
    FIXED_RESET = "fixed_reset"
    ROLLING = "rolling_replenishment"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


def aware(value: datetime | None) -> None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("Time must have a timezone")


@dataclass(frozen=True, slots=True)
class Account:
    id: str
    provider: Provider
    display_name: str
    credential_ref: str | None = None
    enabled: bool = True
    connection_mode: str = "local"

    def __post_init__(self) -> None:
        UUID(self.id)
        if not self.display_name.strip() or len(self.display_name) > 80:
            raise ValueError("Invalid account name")


@dataclass(frozen=True, slots=True)
class QuotaWindow:
    id: str
    source_bucket_id: str
    duration_minutes: int | None
    remaining_percent: float | None
    recovery_kind: RecoveryKind = RecoveryKind.UNKNOWN
    next_recovery_at: datetime | None = None
    used_amount: Decimal | None = None
    total_amount: Decimal | None = None
    unit: str | None = None
    label: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.source_bucket_id:
            raise ValueError("Missing quota window identity")
        if self.duration_minutes is not None and self.duration_minutes <= 0:
            raise ValueError("Invalid window duration")
        if self.remaining_percent is not None and (
            not math.isfinite(self.remaining_percent) or not 0 <= self.remaining_percent <= 100
        ):
            raise ValueError("Invalid quota percentage")
        aware(self.next_recovery_at)
        for amount in (self.used_amount, self.total_amount):
            if amount is not None and (not amount.is_finite() or amount < 0):
                raise ValueError("Invalid quota amount")


@dataclass(frozen=True, slots=True)
class Balance:
    currency: str
    total: Decimal
    granted: Decimal | None = None
    topped_up: Decimal | None = None
    is_available: bool | None = None

    def __post_init__(self) -> None:
        if not self.currency or len(self.currency) > 8:
            raise ValueError("Invalid currency")
        for value in (self.total, self.granted, self.topped_up):
            if value is not None and (not value.is_finite() or value < 0):
                raise ValueError("Invalid balance")


@dataclass(frozen=True, slots=True)
class UsageSnapshot:
    account_id: str
    provider: Provider
    source_kind: str
    windows: tuple[QuotaWindow, ...]
    balances: tuple[Balance, ...]
    last_success_at: datetime
    source_observed_at: datetime | None = None

    def __post_init__(self) -> None:
        UUID(self.account_id)
        aware(self.last_success_at)
        aware(self.source_observed_at)
        ids = [window.id for window in self.windows]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate window identity")
        if self.provider == Provider.DEEPSEEK and self.windows:
            raise ValueError("Balance provider cannot invent quota windows")
        currencies = [balance.currency for balance in self.balances]
        if len(currencies) != len(set(currencies)):
            raise ValueError("Duplicate balance currency")

    def window(self, duration: int, bucket_id: str | None = None) -> QuotaWindow | None:
        """An ambiguous multi-bucket result must never silently pick or average."""
        candidates = [item for item in self.windows if item.duration_minutes == duration
                      and (bucket_id is None or item.source_bucket_id == bucket_id)]
        return candidates[0] if len(candidates) == 1 else None


@dataclass(slots=True)
class ProviderState:
    account: Account
    snapshot: UsageSnapshot | None = None
    status: Status = Status.DISCONNECTED
    last_attempt_at: datetime | None = None
    error: ErrorCode | None = None

    def __post_init__(self) -> None:
        if self.snapshot is not None and (
            self.snapshot.account_id != self.account.id or self.snapshot.provider != self.account.provider
        ):
            raise ValueError("Snapshot belongs to another account")

    @property
    def retained(self) -> bool:
        return self.snapshot is not None and self.status != Status.FRESH
