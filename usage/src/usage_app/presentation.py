"""Small pure projections into the frozen widget's existing information slots."""

from __future__ import annotations

from decimal import Decimal

from quota_visual import QuotaSample

from .models import Provider, ProviderState, QuotaWindow, Status


def window_for(state: ProviderState | None, minutes: int) -> QuotaWindow | None:
    return state.snapshot.window(minutes) if state and state.account.enabled and state.snapshot else None


def compact_amount(total: Decimal, currency: str) -> str:
    prefix = {"CNY": "¥", "USD": "$"}.get(currency, currency + " ")
    if total >= Decimal("1000000000000"):
        return f"{prefix}{total:.2E}"
    if total >= Decimal("100000000"):
        return f"{prefix}{total / Decimal('100000000'):.2f}亿"
    if total >= Decimal("10000"):
        return f"{prefix}{total / Decimal('10000'):.2f}万"
    # Summary precision only; detailed source decimal remains unchanged.
    return prefix + f"{total:.2f}"


def quota_sample(states: dict[Provider, ProviderState]) -> QuotaSample:
    percentages = []
    for provider in (Provider.CODEX, Provider.GLM):
        for minutes in (300, 10080):
            window = window_for(states.get(provider), minutes)
            value = window.remaining_percent if window else None
            percentages.append(round(value, 1) if value is not None else None)
    state = states.get(Provider.DEEPSEEK)
    balances = state.snapshot.balances if state and state.account.enabled and state.snapshot else ()
    balance = compact_amount(balances[0].total, balances[0].currency) if len(balances) == 1 else f"{len(balances)} 币种" if balances else None
    if balance and len(balance) > 8:
        balance = balances[0].currency[:3] + " ·详查"
    return QuotaSample(percentages[0], percentages[1], percentages[2], percentages[3], balance)


def trust_mark(state: ProviderState | None) -> str:
    if state is None or not state.account.enabled or state.status == Status.DISCONNECTED:
        return "断"
    if state.retained:
        return "旧"
    return {Status.LOADING: "读", Status.AUTH_REQUIRED: "权", Status.INCOMPATIBLE: "验",
            Status.OFFLINE: "错", Status.RATE_LIMITED: "等"}.get(state.status, "")
