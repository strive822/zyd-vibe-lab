from datetime import UTC, datetime
from decimal import Decimal

import pytest

from usage_app.models import Account, ErrorCode, Provider, ProviderError, RecoveryKind
from usage_app.parsers import GLM_PERSONAL_MAPPING, GlmWindowMapping, parse_codex, parse_deepseek, parse_glm


def test_codex_uses_duration_and_keeps_buckets(accounts: dict[Provider, Account], now: datetime) -> None:
    bucket = {"primary": {"usedPercent": 20, "windowDurationMins": 10080, "resetsAt": 1800000000},
              "secondary": {"usedPercent": 0, "windowDurationMins": 300, "resetsAt": None}}
    value = parse_codex({"rateLimitsByLimitId": {"codex": bucket, "other": bucket},
                         "rateLimits": {"primary": {"usedPercent": 90, "windowDurationMins": 300}}},
                        accounts[Provider.CODEX], now)
    assert len(value.windows) == 4
    assert value.window(300) is None  # Do not average or silently choose a bucket.
    weekly = value.window(10080, "codex")
    assert weekly and weekly.remaining_percent == 80
    assert weekly.next_recovery_at == datetime.fromtimestamp(1800000000, UTC)
    assert value.window(300, "codex").remaining_percent == 100


@pytest.mark.parametrize("invalid", [-1, 101, float("nan"), float("inf"), True, "50"])
def test_codex_invalid_percentage_is_not_clamped(invalid: object, accounts: dict[Provider, Account], now: datetime) -> None:
    with pytest.raises(ProviderError) as error:
        parse_codex({"rateLimits": {"primary": {"usedPercent": invalid, "windowDurationMins": 300}}},
                    accounts[Provider.CODEX], now)
    assert error.value.code == ErrorCode.INCOMPATIBLE


def test_missing_codex_window_is_unknown(accounts: dict[Provider, Account], now: datetime) -> None:
    snapshot = parse_codex({"rateLimits": {"primary": None, "secondary": {"windowDurationMins": 300}}},
                           accounts[Provider.CODEX], now)
    assert len(snapshot.windows) == 1
    assert snapshot.window(10080) is None
    assert snapshot.window(300).remaining_percent is None
    assert snapshot.window(300).next_recovery_at is None


def test_balance_zero_empty_and_multicurrency_are_distinct(accounts: dict[Provider, Account], now: datetime) -> None:
    snapshot = parse_deepseek({"is_available": False, "balance_infos": [
        {"currency": "CNY", "total_balance": "0.00", "granted_balance": "0", "topped_up_balance": "0"},
        {"currency": "USD", "total_balance": "0.123456789012345678901"}]}, accounts[Provider.DEEPSEEK], now)
    assert not snapshot.windows and len(snapshot.balances) == 2
    assert snapshot.balances[0].total == Decimal("0.00")
    assert snapshot.balances[1].total == Decimal("0.123456789012345678901")
    assert snapshot.balances[0].is_available is False
    empty = parse_deepseek({"is_available": True, "balance_infos": []}, accounts[Provider.DEEPSEEK], now)
    assert empty.balances == ()


@pytest.mark.parametrize("invalid", ["-1", "NaN", "Infinity", 12.34, None, "bad"])
def test_balance_rejects_invalid_amounts(invalid: object, accounts: dict[Provider, Account], now: datetime) -> None:
    with pytest.raises(ProviderError):
        parse_deepseek({"is_available": True, "balance_infos": [{"currency": "CNY", "total_balance": invalid}]},
                       accounts[Provider.DEEPSEEK], now)


def test_glm_needs_verified_mapping_and_never_uses_mcp(accounts: dict[Provider, Account], now: datetime) -> None:
    # Synthetic contract fixture. These names are not claims about the live API.
    raw = {"data": {"limits": [
        {"type": "verified-five", "percentage": 30, "nextAt": 1800000000000},
        {"type": "verified-week", "percentage": 40},
        {"type": "TIME_LIMIT", "percentage": 100}]}}
    with pytest.raises(ProviderError):
        parse_glm(raw, accounts[Provider.GLM], now)
    rules = (GlmWindowMapping("verified-five", 300, True, "nextAt", True, RecoveryKind.ROLLING),
             GlmWindowMapping("verified-week", 10080, False))
    snapshot = parse_glm(raw, accounts[Provider.GLM], now, rules)
    assert len(snapshot.windows) == 2
    assert snapshot.window(300).remaining_percent == 70
    assert snapshot.window(300).recovery_kind == RecoveryKind.ROLLING
    assert snapshot.window(300).next_recovery_at == datetime.fromtimestamp(1800000000, UTC)
    assert snapshot.window(10080).remaining_percent == 40
    assert snapshot.window(10080).next_recovery_at is None


def test_adapter_account_isolation(accounts: dict[Provider, Account], now: datetime) -> None:
    with pytest.raises(ValueError):
        parse_codex({}, accounts[Provider.GLM], now)


def test_glm_same_type_windows_match_identity_not_order_or_total(accounts: dict[Provider, Account], now: datetime) -> None:
    raw = {"data": {"limits": [
        {"type": "CREDIT_LIMIT", "unit": 6, "number": 1, "percentage": 87.5, "usage": 7, "nextResetTime": 1800000000000},
        {"type": "TIME_LIMIT", "unit": 5, "number": 1, "percentage": 99},
        {"type": "CREDIT_LIMIT", "unit": 3, "number": 5, "percentage": 12.5, "usage": 999999},
        {"type": "CREDIT_LIMIT", "unit": 5, "number": 1, "percentage": 0}]}}
    snapshot = parse_glm(raw, accounts[Provider.GLM], now, GLM_PERSONAL_MAPPING)
    assert len(snapshot.windows) == 2 and len({item.id for item in snapshot.windows}) == 2
    assert snapshot.window(300).remaining_percent == 87.5
    assert snapshot.window(300).next_recovery_at is None
    assert snapshot.window(300).recovery_kind == RecoveryKind.UNKNOWN
    assert snapshot.window(10080).remaining_percent == 12.5
    assert snapshot.window(10080).next_recovery_at == datetime.fromtimestamp(1800000000, UTC)
    assert snapshot.window(10080).recovery_kind == RecoveryKind.FIXED_RESET


def test_glm_duplicate_window_is_rejected(accounts: dict[Provider, Account], now: datetime) -> None:
    row = {"type": "CREDIT_LIMIT", "unit": 3, "number": 5, "percentage": 30}
    with pytest.raises(ProviderError):
        parse_glm({"data": {"limits": [row, row]}}, accounts[Provider.GLM], now, GLM_PERSONAL_MAPPING)


@pytest.mark.parametrize("unit,count", [(3, 1), (6, 5), (5, 1), (True, 5), (3, True), ("3", 5), (3, None)])
def test_glm_unverified_identity_is_not_fabricated(unit: object, count: object, accounts: dict[Provider, Account], now: datetime) -> None:
    with pytest.raises(ProviderError):
        parse_glm({"data": {"limits": [{"type": "CREDIT_LIMIT", "unit": unit, "number": count, "percentage": 0}]}},
                  accounts[Provider.GLM], now, GLM_PERSONAL_MAPPING)


def test_codex_empty_unrecognized_body_is_not_success(accounts: dict[Provider, Account], now: datetime) -> None:
    with pytest.raises(ProviderError):
        parse_codex({}, accounts[Provider.CODEX], now)
    assert parse_codex({"rateLimits": None}, accounts[Provider.CODEX], now).windows == ()
