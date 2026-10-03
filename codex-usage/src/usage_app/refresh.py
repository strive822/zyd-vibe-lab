"""Single-flight, backoff and generation guards, independent of Qt/network I/O."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from random import random
from typing import Callable

from .models import Account, ErrorCode, ProviderError, ProviderState, Status, UsageSnapshot


REFRESH_INTERVAL_SECONDS = 5


@dataclass(frozen=True, slots=True)
class RequestTicket:
    account_id: str
    generation: int
    sequence: int


class RefreshCoordinator:
    def __init__(self, *, jitter: Callable[[], float] = random) -> None:
        self.states: dict[str, ProviderState] = {}
        self._generation: dict[str, int] = {}
        self._pending: dict[str, RequestTicket] = {}
        self._due: dict[str, float] = {}
        self._failures: dict[str, int] = {}
        self._paused: set[str] = set()
        self._sequence = 0
        self._jitter = jitter
        self._cooling: set[str] = set()
        self._last_success_mono: dict[str, float] = {}

    def register(self, account: Account, cached: UsageSnapshot | None = None) -> None:
        if any(state.account.provider == account.provider and key != account.id for key, state in self.states.items()):
            raise ValueError("Only one account per provider is supported")
        if account.id in self.states:
            if self.states[account.id].account == account:
                return
            self.remove(account.id)
        self._generation[account.id] = self._generation.get(account.id, 0) + 1
        self.states[account.id] = ProviderState(account, cached, Status.STALE if cached else Status.DISCONNECTED)
        self._due[account.id] = 0

    def remove(self, account_id: str) -> None:
        self.cancel(account_id)
        self.states.pop(account_id, None)
        self._due.pop(account_id, None)
        self._failures.pop(account_id, None)
        self._paused.discard(account_id)
        self._cooling.discard(account_id)
        self._last_success_mono.pop(account_id, None)

    def cancel(self, account_id: str) -> None:
        self._generation[account_id] = self._generation.get(account_id, 0) + 1
        self._pending.pop(account_id, None)
        state = self.states.get(account_id)
        if state is not None:
            state.status = Status.STALE if state.snapshot else Status.DISCONNECTED

    def begin(self, account_id: str, now: datetime, monotonic_now: float, *, manual: bool = False) -> RequestTicket | None:
        state = self.states[account_id]
        if not state.account.enabled or account_id in self._pending or account_id in self._paused:
            return None
        if monotonic_now < self._due.get(account_id, 0) and (not manual or account_id in self._cooling):
            return None  # Manual refresh respects Retry-After and failure cooldown.
        self._sequence += 1
        ticket = RequestTicket(account_id, self._generation[account_id], self._sequence)
        self._pending[account_id] = ticket
        state.status = Status.LOADING
        state.last_attempt_at = now
        state.error = None
        return ticket

    def _accept(self, ticket: RequestTicket) -> ProviderState | None:
        if self._pending.get(ticket.account_id) != ticket:
            return None
        return self.states.get(ticket.account_id)

    def succeed(self, ticket: RequestTicket, snapshot: UsageSnapshot, monotonic_now: float, *, expanded: bool) -> bool:
        state = self._accept(ticket)
        if state is None:
            return False
        if snapshot.account_id != ticket.account_id or snapshot.provider != state.account.provider:
            raise ValueError("Response belongs to another account")
        self._pending.pop(ticket.account_id)
        state.snapshot = snapshot
        state.status = Status.FRESH
        state.error = None
        self._failures[ticket.account_id] = 0
        self._cooling.discard(ticket.account_id)
        self._last_success_mono[ticket.account_id] = monotonic_now
        self._due[ticket.account_id] = monotonic_now + REFRESH_INTERVAL_SECONDS
        return True

    def fail(self, ticket: RequestTicket, error: ProviderError, monotonic_now: float) -> bool:
        state = self._accept(ticket)
        if state is None:
            return False
        self._pending.pop(ticket.account_id)
        state.error = error.code
        if error.code in (ErrorCode.AUTH_REQUIRED, ErrorCode.FORBIDDEN, ErrorCode.UNCONFIGURED):
            state.status = Status.AUTH_REQUIRED if error.code != ErrorCode.UNCONFIGURED else Status.DISCONNECTED
            self._paused.add(ticket.account_id)
        else:
            state.status = Status.RATE_LIMITED if error.code == ErrorCode.RATE_LIMITED else (
                Status.INCOMPATIBLE if error.code == ErrorCode.INCOMPATIBLE else Status.STALE if state.snapshot else Status.OFFLINE)
            failures = self._failures.get(ticket.account_id, 0) + 1
            self._failures[ticket.account_id] = failures
            delay = (30, 60, 120, 300)[min(failures - 1, 3)]
            self._cooling.add(ticket.account_id)
            self._due[ticket.account_id] = monotonic_now + max(delay + max(0, min(1, self._jitter())) * 3, error.retry_after or 0)
        return True

    def due_in(self, account_id: str, monotonic_now: float) -> float:
        return max(0, self._due.get(account_id, 0) - monotonic_now)

    def authorization_changed(self, account_id: str) -> None:
        self.cancel(account_id)
        self._paused.discard(account_id)
        self._failures.pop(account_id, None)
        self._due[account_id] = 0
        self._cooling.discard(account_id)

    def set_expanded(self, expanded: bool) -> None:
        for account_id, when in self._last_success_mono.items():
            if account_id not in self._cooling and account_id not in self._paused:
                self._due[account_id] = when + REFRESH_INTERVAL_SECONDS
