from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from usage_app.models import Account, ErrorCode, Provider, ProviderError, Status, UsageSnapshot
from usage_app.parsers import parse_codex, parse_deepseek
from usage_app.refresh import RefreshCoordinator


def test_single_flight_failure_retains_data_and_other_provider(accounts: dict[Provider, Account], now: datetime) -> None:
    coordinator = RefreshCoordinator(jitter=lambda: 0)
    codex, deepseek = accounts[Provider.CODEX], accounts[Provider.DEEPSEEK]
    old = parse_codex({"rateLimits": None}, codex, now)
    other = parse_deepseek({"is_available": True, "balance_infos": []}, deepseek, now)
    coordinator.register(codex, old)
    coordinator.register(deepseek, other)
    later = now + timedelta(hours=1)
    ticket = coordinator.begin(codex.id, later, 100)
    assert ticket and coordinator.begin(codex.id, later, 100) is None
    assert coordinator.fail(ticket, ProviderError(ErrorCode.NETWORK), 100)
    state = coordinator.states[codex.id]
    assert state.snapshot is old and state.snapshot.last_success_at == now
    assert state.last_attempt_at == later and state.retained
    assert coordinator.states[deepseek.id].snapshot is other
    assert coordinator.begin(codex.id, later, 129) is None
    retry = coordinator.begin(codex.id, later, 130)
    assert retry
    fresh = parse_codex({"rateLimits": None}, codex, later)
    assert coordinator.succeed(retry, fresh, 130, expanded=True)
    assert state.status == Status.FRESH and coordinator.due_in(codex.id, 130) == 5


def test_late_response_cannot_cross_changed_credentials(accounts: dict[Provider, Account], now: datetime) -> None:
    coordinator = RefreshCoordinator(jitter=lambda: 0)
    account = accounts[Provider.CODEX]
    coordinator.register(account)
    ticket = coordinator.begin(account.id, now, 0)
    old = parse_codex({"rateLimits": None}, account, now)
    coordinator.register(replace(account, credential_ref="new-reference"))
    assert ticket and not coordinator.succeed(ticket, old, 1, expanded=False)
    assert coordinator.states[account.id].snapshot is None
    newer = coordinator.begin(account.id, now, 1)
    assert newer and newer.generation > ticket.generation


def test_retry_after_and_auth_pause_cannot_be_bypassed(accounts: dict[Provider, Account], now: datetime) -> None:
    coordinator = RefreshCoordinator(jitter=lambda: 0)
    account = accounts[Provider.CODEX]
    coordinator.register(account)
    ticket = coordinator.begin(account.id, now, 0)
    assert ticket
    coordinator.fail(ticket, ProviderError(ErrorCode.RATE_LIMITED, 900), 0)
    assert coordinator.begin(account.id, now + timedelta(days=1), 899) is None
    ticket = coordinator.begin(account.id, now, 900)
    assert ticket
    coordinator.fail(ticket, ProviderError(ErrorCode.AUTH_REQUIRED), 900)
    assert coordinator.begin(account.id, now, 100000) is None
    coordinator.authorization_changed(account.id)
    assert coordinator.begin(account.id, now, 100001)


@pytest.mark.parametrize("provider", list(Provider))
def test_missing_codex_installation_retries_but_missing_api_keys_stay_paused(accounts, now, provider):
    coordinator = RefreshCoordinator(jitter=lambda: 0)
    account = accounts[provider]
    cached = UsageSnapshot(account.id, provider, "synthetic", (), (), now)
    coordinator.register(account, cached)
    ticket = coordinator.begin(account.id, now, 0)
    assert ticket and coordinator.fail(ticket, ProviderError(ErrorCode.UNCONFIGURED), 0)
    assert coordinator.states[account.id].snapshot is cached
    assert coordinator.begin(account.id, now, 29, manual=True) is None
    if provider != Provider.CODEX:
        assert coordinator.begin(account.id, now, 100000) is None
        return
    retry = coordinator.begin(account.id, now, 30)
    assert retry and coordinator.fail(retry, ProviderError(ErrorCode.UNCONFIGURED), 30)
    assert coordinator.begin(account.id, now, 89, manual=True) is None
    retry = coordinator.begin(account.id, now, 90)
    fresh = replace(cached, last_success_at=now + timedelta(seconds=90))
    assert retry and coordinator.succeed(retry, fresh, 90, expanded=False)
    assert coordinator.states[account.id].status == Status.FRESH
    assert coordinator.due_in(account.id, 90) == 5


def test_wrong_account_and_duplicate_provider_rejected(accounts: dict[Provider, Account], now: datetime) -> None:
    coordinator = RefreshCoordinator(jitter=lambda: 0)
    account = accounts[Provider.CODEX]
    coordinator.register(account)
    ticket = coordinator.begin(account.id, now, 0)
    other = replace(account, id="00000000-0000-4000-8000-000000000009")
    with pytest.raises(ValueError):
        coordinator.register(other)
    assert ticket
    with pytest.raises(ValueError):
        coordinator.succeed(ticket, parse_codex({"rateLimits": None}, other, now), 0, expanded=True)
    coordinator.cancel(account.id)
    assert not coordinator.succeed(ticket, parse_codex({"rateLimits": None}, account, now), 0, expanded=True)


def test_all_providers_keep_cached_data_and_back_off_through_repeated_failure(accounts: dict[Provider, Account], now: datetime) -> None:
    coordinator = RefreshCoordinator(jitter=lambda: 0)
    cached = {provider: UsageSnapshot(account.id, provider, "synthetic", (), (), now)
              for provider, account in accounts.items()}
    for provider, account in accounts.items():
        coordinator.register(account, cached[provider])
        ticket = coordinator.begin(account.id, now, 0)
        assert ticket and coordinator.succeed(ticket, cached[provider], 0, expanded=False)

    errors = {Provider.CODEX: ErrorCode.NETWORK, Provider.GLM: ErrorCode.TIMEOUT, Provider.DEEPSEEK: ErrorCode.SERVICE}
    elapsed = 5
    # Repeated retries reach the cap; neither wall-clock jumps nor repeatedly
    # opening the leaf or pressing Refresh is allowed to shorten this cooldown.
    for delay in (30, 60, 120, 300, 300):
        for provider, account in accounts.items():
            ticket = coordinator.begin(account.id, now + timedelta(seconds=elapsed), elapsed)
            assert ticket and coordinator.fail(ticket, ProviderError(errors[provider]), elapsed)
            state = coordinator.states[account.id]
            assert state.snapshot is cached[provider] and state.snapshot.last_success_at == now
            assert state.status == Status.STALE and state.retained
        for second in range(delay):
            coordinator.set_expanded(second % 2 == 0)
            for account in accounts.values():
                assert coordinator.begin(account.id, now + timedelta(days=1), elapsed + second, manual=True) is None
        elapsed += delay

    codex = accounts[Provider.CODEX]
    recovery = coordinator.begin(codex.id, now + timedelta(seconds=elapsed), elapsed)
    fresh = replace(cached[Provider.CODEX], last_success_at=now + timedelta(seconds=elapsed))
    assert recovery and coordinator.succeed(recovery, fresh, elapsed, expanded=True)
    assert coordinator.due_in(codex.id, elapsed) == 5
    for provider in (Provider.GLM, Provider.DEEPSEEK):
        state = coordinator.states[accounts[provider].id]
        assert state.status == Status.STALE and state.snapshot is cached[provider]


@pytest.mark.parametrize("provider", list(Provider))
@pytest.mark.parametrize("expanded", [False, True])
def test_five_second_cadence_survives_hover_and_merges_inflight_requests(
    accounts: dict[Provider, Account], now: datetime, provider: Provider, expanded: bool,
) -> None:
    coordinator = RefreshCoordinator(jitter=lambda: 0)
    account = accounts[provider]
    coordinator.register(account)
    snapshot = UsageSnapshot(account.id, provider, "synthetic", (), (), now)
    ticket = coordinator.begin(account.id, now, 0)
    assert ticket and coordinator.succeed(ticket, snapshot, 0, expanded=expanded)
    for second in range(1, 5):
        coordinator.set_expanded(not expanded if second % 2 else expanded)
        assert coordinator.begin(account.id, now + timedelta(seconds=second), second) is None
        assert coordinator.due_in(account.id, second) == 5 - second
    next_ticket = coordinator.begin(account.id, now + timedelta(seconds=5), 5)
    assert next_ticket
    assert coordinator.begin(account.id, now + timedelta(seconds=6), 6, manual=True) is None
    assert coordinator.begin(account.id, now + timedelta(seconds=10), 10) is None
    # The next interval starts after a slow response completes, with no backlog.
    fresh = replace(snapshot, last_success_at=now + timedelta(seconds=10))
    assert coordinator.succeed(next_ticket, fresh, 10, expanded=not expanded)
    assert coordinator.due_in(account.id, 10) == 5
