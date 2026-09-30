"""Configuration references and atomic credential replacement, one account/provider."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import UUID, uuid4

from .credentials import CredentialError, SecretStore, new_reference, validate_reference
from .models import Account, Provider, ProviderError
from .parsers import items, object_map
from .storage import JsonStore, SnapshotCache, StorageError


class AccountStore:
    def __init__(self, data_dir: Path, secrets: SecretStore):
        self.store = JsonStore(data_dir / "config.json")
        self.cache = SnapshotCache(data_dir)
        self.secrets = secrets
        self.cleanup_warning: str | None = None

    def load(self) -> tuple[Account, ...]:
        value = self.store.load()
        if value is None:
            return ()
        try:
            accounts = []
            providers = set()
            identities = set()
            for raw in items(value.get("accounts", [])):
                entry = object_map(raw)
                provider = Provider(str(entry["provider"]))
                enabled = entry.get("enabled", True)
                if not isinstance(enabled, bool):
                    raise ValueError
                reference = entry.get("credentialRef")
                account = Account(str(entry["id"]), provider, str(entry["displayName"]),
                                  str(reference) if reference is not None else None,
                                  enabled, str(entry.get("connectionMode", "local")))
                if account.provider in providers or account.id in identities:
                    raise ValueError
                if account.credential_ref:
                    validate_reference(account.credential_ref)
                    if account.credential_ref.split("/")[1:3] != [provider.value, account.id]:
                        raise ValueError
                providers.add(provider)
                identities.add(account.id)
                accounts.append(account)
            return tuple(accounts)
        except (KeyError, ValueError, ProviderError, CredentialError) as exc:
            raise StorageError("Invalid account configuration; file was preserved") from exc

    def save(self, accounts: tuple[Account, ...], *, cleanup: Account | None = None) -> None:
        if len({account.provider for account in accounts}) != len(accounts):
            raise StorageError("Only one account per provider is supported")
        value = self.store.load() or {}
        value["accounts"] = [{"id": account.id, "provider": account.provider.value,
                              "displayName": account.display_name, "connectionMode": account.connection_mode,
                              "credentialRef": account.credential_ref, "enabled": account.enabled}
                             for account in accounts]
        if cleanup:
            pending = list(items(value.get("accountCleanup", [])))
            pending.append({"accountId": cleanup.id, "credentialRef": cleanup.credential_ref})
            value["accountCleanup"] = pending
        self.store.save(value)

    def ensure_defaults(self) -> tuple[Account, ...]:
        existing = {account.provider: account for account in self.load()}
        result = tuple(existing.get(provider) or Account(str(uuid4()), provider,
                       {Provider.CODEX: "Codex", Provider.GLM: "GLM", Provider.DEEPSEEK: "DeepSeek"}[provider])
                       for provider in Provider)
        if len(existing) != len(result):
            self.save(result)
        return result

    def connect_key(self, provider: Provider, secret: str) -> Account:
        if provider == Provider.CODEX:
            raise ValueError("Codex uses the official local authentication context")
        accounts = self.ensure_defaults()
        previous = next(account for account in accounts if account.provider == provider)
        # A new key may belong to a different remote account. New identity means
        # an old cached response cannot be displayed for it even if cleanup fails.
        new_id = str(uuid4())
        reference = new_reference(provider, new_id)
        self.secrets.write(reference, secret)
        updated = replace(previous, id=new_id, credential_ref=reference, enabled=True, connection_mode="key")
        try:
            self.save(tuple(updated if account.id == previous.id else account for account in accounts), cleanup=previous)
        except StorageError:
            self.secrets.delete(reference)
            raise
        # Configuration committed first; retain the previous key if commit fails.
        self.retry_cleanup()
        return updated

    def disconnect(self, provider: Provider) -> None:
        accounts = self.load()
        previous = next((account for account in accounts if account.provider == provider), None)
        if previous is None:
            return
        updated = replace(previous, credential_ref=None, enabled=False)
        self.save(tuple(updated if account.id == previous.id else account for account in accounts), cleanup=previous)
        self.retry_cleanup()

    def set_codex_enabled(self, enabled: bool) -> None:
        previous = self.ensure_defaults()
        self.save(tuple(replace(item, enabled=enabled) if item.provider == Provider.CODEX else item for item in previous))

    def retry_cleanup(self) -> bool:
        """Committed config stays authoritative even if old local cleanup fails.

        Only owned references/account IDs are accepted. Retry metadata contains
        references, never a key; no active account's key/cache can be removed.
        """
        self.cleanup_warning = None
        try:
            data = self.store.load() or {}
            pending = items(data.get("accountCleanup", []))
            if not pending:
                return True
            active = self.load()
            active_refs = {item.credential_ref for item in active if item.credential_ref}
            active_ids = {item.id for item in active if item.enabled}
            remaining: list[object] = []
            for raw in pending:
                entry = object_map(raw)
                identity = str(entry.get("accountId", ""))
                if str(UUID(identity)) != identity:
                    raise ValueError
                reference = entry.get("credentialRef")
                if reference is not None:
                    if not isinstance(reference, str):
                        raise ValueError
                    validate_reference(reference)
                    if reference.split("/")[2] != identity:
                        raise ValueError
                if identity in active_ids and reference is None:
                    continue  # Codex re-enabled: its cache now belongs to the active session.
                if identity in active_ids or reference and reference in active_refs:
                    raise ValueError
                try:
                    if reference:
                        self.secrets.delete(reference)
                    self.cache.remove(identity)
                except (StorageError, CredentialError):
                    remaining.append(raw)
            data["accountCleanup"] = remaining
            self.store.save(data)
            if remaining:
                self.cleanup_warning = "账号已保存；旧本机密钥或缓存尚未清理，请重试清理"
            return not remaining
        except (StorageError, CredentialError, ProviderError, ValueError):
            self.cleanup_warning = "账号已保存；旧本机数据清理未完成，原文件已保留"
            return False
