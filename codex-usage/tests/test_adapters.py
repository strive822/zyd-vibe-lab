from datetime import UTC, datetime

import pytest

from usage_app.adapters import decode_response, http_error, retry_after
from usage_app.credentials import CredentialError, new_reference, validate_reference
from usage_app.models import ErrorCode, Provider, ProviderError


@pytest.mark.parametrize("status,code", [(401, ErrorCode.AUTH_REQUIRED), (403, ErrorCode.FORBIDDEN),
                                         (429, ErrorCode.RATE_LIMITED), (503, ErrorCode.SERVICE),
                                         (302, ErrorCode.INCOMPATIBLE), (404, ErrorCode.INCOMPATIBLE)])
def test_http_failures_are_safe_and_classified(status, code, now):
    error = http_error(status, "120", now)
    assert error and error.code == code
    assert "120" not in str(error)
    if status == 429:
        assert error.retry_after == 120


def test_retry_after_date_and_bad_values():
    now = datetime(2026, 9, 30, 1, 0, tzinfo=UTC)
    assert retry_after("Wed, 30 Sep 2026 01:05:00 GMT", now) == 300
    for value in ("nan", "inf", "bad", ""):
        assert retry_after(value, now) is None
    assert retry_after("-1", now) == 0
    assert http_error(200, "", now) is None


def test_invalid_and_oversized_responses_are_not_retained():
    for value in (b"not json", b"\xff", b" " * (1024 * 1024 + 1)):
        with pytest.raises(ProviderError) as error:
            decode_response(value)
        assert error.value.code == ErrorCode.INCOMPATIBLE


def test_credential_store_only_accepts_application_namespace():
    account_id = "00000000-0000-4000-8000-000000000001"
    validate_reference(new_reference(Provider.GLM, account_id))
    for reference in ("OtherApp/key", "Duizhaoye/glm/not-uuid/key", "Duizhaoye/other/" + account_id):
        with pytest.raises(CredentialError):
            validate_reference(reference)
