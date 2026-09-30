"""Event-loop coordinator; background I/O never drives presentation clocks."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer, Signal

from .accounts import AccountStore
from .adapters import CodexAdapter, HttpQuotaAdapter, ProviderAdapter
from .credentials import WindowsCredentialStore
from .diagnostics import DiagnosticLog
from .models import Account, Provider, ProviderError, ProviderState, UsageSnapshot
from .refresh import RefreshCoordinator, RequestTicket
from .storage import SnapshotCache, StorageError


class UsageRuntime(QObject):
    changed = Signal()
    storage_failed = Signal(str)

    def __init__(self, data_dir: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.data_dir = data_dir
        self.diagnostics = DiagnosticLog(data_dir)
        self.secrets = WindowsCredentialStore()
        self.accounts = AccountStore(data_dir, self.secrets)
        self.accounts.retry_cleanup()
        self.cache = SnapshotCache(data_dir)
        self.refresh = RefreshCoordinator()
        self.expanded = False
        self._stopped = False
        self.adapters: dict[Provider, ProviderAdapter] = {
            Provider.CODEX: CodexAdapter(self),
            Provider.GLM: HttpQuotaAdapter(Provider.GLM, self.secrets, self),
            Provider.DEEPSEEK: HttpQuotaAdapter(Provider.DEEPSEEK, self.secrets, self),
        }
        self._confirmed_events: set[tuple[str, str, datetime]] = set()
        for adapter in self.adapters.values():
            adapter.succeeded.connect(self._succeeded)
            adapter.failed.connect(self._failed)
        self.reload_accounts()
        self._config_reload = QTimer(self)
        self._config_reload.setSingleShot(True)
        self._config_reload.timeout.connect(self._reload_configuration)
        self._config_watch = QFileSystemWatcher(self)
        self._config_watch.addPath(str(self.accounts.store.path))
        self._config_watch.fileChanged.connect(lambda path: self._config_reload.start(120))
        self._poll = QTimer(self)
        self._poll.timeout.connect(self.poll)
        self._poll.start(1000)
        QTimer.singleShot(0, self.poll)

    @property
    def states(self) -> dict[Provider, ProviderState]:
        return {state.account.provider: state for state in self.refresh.states.values()}

    def reload_accounts(self) -> None:
        accounts = self.accounts.ensure_defaults()
        old = self.refresh.states.copy()
        for account_id, state in old.items():
            if state.account not in accounts:
                self.adapters[state.account.provider].cancel(account_id)
                self.refresh.remove(account_id)
        for account in accounts:
            if account.id not in self.refresh.states:
                try:
                    cached = self.cache.load(account)
                except StorageError as error:
                    cached = None
                    self.diagnostics.write("storage_failed", provider=account.provider, error=error)
                    self.storage_failed.emit(str(error))
                self.refresh.register(account, cached)
        self.changed.emit()

    def _reload_configuration(self) -> None:
        if self._stopped:
            return
        try:
            self.reload_accounts()
        except StorageError as error:
            self.diagnostics.write("storage_failed", error=error)
            self.storage_failed.emit(str(error))
        path = str(self.accounts.store.path)
        if self.accounts.store.path.exists() and path not in self._config_watch.files():
            self._config_watch.addPath(path)  # Atomic replacement invalidates the old file watch.

    def _request(self, account: Account, *, manual: bool = False) -> None:
        if self._stopped:
            return
        ticket = self.refresh.begin(account.id, datetime.now(UTC), time.monotonic(), manual=manual)
        if ticket:
            self.changed.emit()
            self.adapters[account.provider].read(account, ticket)

    def poll(self) -> None:
        if self._stopped:
            return
        now = datetime.now(UTC)
        for state in tuple(self.refresh.states.values()):
            # A source recovery event gets one verification per successful
            # observation; it never manufactures refreshed percentages locally.
            if state.snapshot:
                for window in state.snapshot.windows:
                    at = window.next_recovery_at
                    if at and at <= now:
                        key = (state.account.id, window.id, at)
                        if key not in self._confirmed_events:
                            self._confirmed_events.add(key)
                            self._request(state.account, manual=True)
            self._request(state.account)

    def refresh_now(self) -> None:
        for state in tuple(self.refresh.states.values()):
            self._request(state.account, manual=True)

    def set_expanded(self, expanded: bool) -> None:
        if expanded != self.expanded:
            self.expanded = expanded
            self.refresh.set_expanded(expanded)

    def _succeeded(self, ticket: RequestTicket, snapshot: UsageSnapshot) -> None:
        if self.refresh.succeed(ticket, snapshot, time.monotonic(), expanded=self.expanded):
            self.diagnostics.write("refresh_ok", provider=snapshot.provider)
            try:
                self.cache.save(snapshot)
            except StorageError as error:
                self.diagnostics.write("storage_failed", provider=snapshot.provider, error=error)
                self.storage_failed.emit(str(error))
            self.changed.emit()

    def _failed(self, ticket: RequestTicket, error: ProviderError) -> None:
        if self.refresh.fail(ticket, error, time.monotonic()):
            state = self.refresh.states.get(ticket.account_id)
            self.diagnostics.write("refresh_failed", provider=state.account.provider if state else None, code=error.code)
            self.changed.emit()

    def stop(self) -> None:
        self._stopped = True
        self._poll.stop()
        self._config_reload.stop()
        for account_id, state in tuple(self.refresh.states.items()):
            self.refresh.cancel(account_id)
            self.adapters[state.account.provider].cancel(account_id)
