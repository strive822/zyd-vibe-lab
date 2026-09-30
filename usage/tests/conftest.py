from datetime import UTC, datetime

import pytest

from usage_app.models import Account, Provider


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 9, 30, 5, 0, tzinfo=UTC)


@pytest.fixture
def accounts() -> dict[Provider, Account]:
    return {provider: Account(f"00000000-0000-4000-8000-00000000000{index}", provider, provider.value)
            for index, provider in enumerate(Provider)}
