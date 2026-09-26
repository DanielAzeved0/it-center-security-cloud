from datetime import datetime, timedelta, timezone

import pytest

from app.database import get_connection
from app.repositories.revoked_tokens import (
    is_token_revoked,
    purge_expired_revoked_tokens,
    revoke_token,
)


@pytest.fixture(autouse=True)
def clean_revoked_tokens():
    with get_connection() as conn:
        conn.execute("TRUNCATE TABLE revoked_tokens")
    yield
    with get_connection() as conn:
        conn.execute("TRUNCATE TABLE revoked_tokens")


def test_is_token_revoked_returns_false_for_non_revoked_token():
    dummy_hash = "a" * 64
    assert is_token_revoked(dummy_hash) is False


def test_revoke_token_and_verify_is_revoked():
    token_hash = "b" * 64
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    revoke_token(token_hash, expires_at)

    assert is_token_revoked(token_hash) is True


def test_revoke_token_on_conflict_does_not_fail():
    token_hash = "c" * 64
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    revoke_token(token_hash, expires_at)
    # Revoking again should be a no-op due to ON CONFLICT DO NOTHING
    revoke_token(token_hash, expires_at)

    assert is_token_revoked(token_hash) is True


def test_purge_expired_revoked_tokens():
    now = datetime.now(timezone.utc)
    expired_hash = "d" * 64
    active_hash = "e" * 64

    revoke_token(expired_hash, now - timedelta(minutes=5))
    revoke_token(active_hash, now + timedelta(hours=1))

    deleted_count = purge_expired_revoked_tokens()
    assert deleted_count == 1

    assert is_token_revoked(expired_hash) is False
    assert is_token_revoked(active_hash) is True
