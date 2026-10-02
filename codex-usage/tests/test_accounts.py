from pathlib import Path

import pytest

from usage_app.accounts import AccountStore
from usage_app.credentials import CredentialError
from usage_app.models import Provider
from usage_app.storage import StorageError


class MemorySecrets:
    def __init__(self):
        self.values = {}

    def write(self, reference, secret):
        self.values[reference] = secret

    def read(self, reference):
        return self.values.get(reference)

    def delete(self, reference):
        self.values.pop(reference, None)


def test_key_rotation_isolated_and_no_plaintext_config(tmp_path: Path):
    secrets = MemorySecrets()
    store = AccountStore(tmp_path, secrets)
    initial = store.ensure_defaults()
    account = store.connect_key(Provider.GLM, "synthetic-key-a")
    assert len(store.load()) == 3 and len(secrets.values) == 1
    assert "synthetic-key" not in store.store.path.read_text()
    newer = store.connect_key(Provider.GLM, "synthetic-key-b")
    assert newer.id != account.id and newer.credential_ref != account.credential_ref
    assert len(secrets.values) == 1 and secrets.read(account.credential_ref) is None
    others = [item for item in initial if item.provider != Provider.GLM]
    assert [item for item in store.load() if item.provider != Provider.GLM] == others


def test_save_failure_cleans_staged_key_and_preserves_previous(tmp_path: Path, monkeypatch):
    secrets = MemorySecrets()
    store = AccountStore(tmp_path, secrets)
    account = store.connect_key(Provider.DEEPSEEK, "synthetic-old")
    original = store.store.path.read_bytes()
    def fail(value, **kwargs):
        raise StorageError("synthetic disk failure")
    monkeypatch.setattr(store, "save", fail)
    with pytest.raises(StorageError):
        store.connect_key(Provider.DEEPSEEK, "synthetic-new")
    assert store.store.path.read_bytes() == original
    assert secrets.values == {account.credential_ref: "synthetic-old"}


def test_unbind_affects_only_one_provider(tmp_path: Path):
    secrets = MemorySecrets()
    store = AccountStore(tmp_path, secrets)
    glm = store.connect_key(Provider.GLM, "synthetic-glm")
    deepseek = store.connect_key(Provider.DEEPSEEK, "synthetic-deepseek")
    store.disconnect(Provider.GLM)
    assert secrets.read(glm.credential_ref) is None
    assert secrets.read(deepseek.credential_ref) == "synthetic-deepseek"
    assert next(item for item in store.load() if item.provider == Provider.DEEPSEEK) == deepseek


def test_committed_new_account_survives_cleanup_failure_and_can_retry(tmp_path: Path, monkeypatch):
    secrets = MemorySecrets()
    store = AccountStore(tmp_path, secrets)
    old = store.connect_key(Provider.GLM, "synthetic-old")
    original = secrets.delete
    def fail(reference):
        raise CredentialError("synthetic delete failure")
    monkeypatch.setattr(secrets, "delete", fail)
    current = store.connect_key(Provider.GLM, "synthetic-new")
    assert next(item for item in store.load() if item.provider == Provider.GLM) == current
    assert current.id != old.id and store.cleanup_warning
    assert store.store.load()["accountCleanup"] and "synthetic-new" not in store.store.path.read_text()
    monkeypatch.setattr(secrets, "delete", original)
    assert store.retry_cleanup() and not store.cleanup_warning
    assert secrets.read(old.credential_ref) is None and secrets.read(current.credential_ref) == "synthetic-new"


def test_cleanup_cannot_target_current_account_or_foreign_credentials(tmp_path: Path):
    secrets = MemorySecrets()
    store = AccountStore(tmp_path, secrets)
    active = store.connect_key(Provider.DEEPSEEK, "synthetic-active")
    for reference in (active.credential_ref, "foreign-credential-target"):
        data = store.store.load()
        data["accountCleanup"] = [{"accountId": active.id, "credentialRef": reference}]
        store.store.save(data)
        assert not store.retry_cleanup()
        assert secrets.read(active.credential_ref) == "synthetic-active"
