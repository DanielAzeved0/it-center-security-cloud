import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import Settings


@pytest.fixture(autouse=True)
def clean_database():
    """No database needed for config tests."""
    pass


@pytest.mark.parametrize("insecure_value", ["too-short", None, "", "change-me", "CHANGE_ME", "replace-me"])
def test_production_rejects_insecure_or_short_agent_api_key(monkeypatch, insecure_value):
    monkeypatch.setenv("APP_ENV", "production")
    if insecure_value is None:
        monkeypatch.delenv("AGENT_API_KEY", raising=False)
    else:
        monkeypatch.setenv("AGENT_API_KEY", insecure_value)
    monkeypatch.setenv("AUTH_TOKEN_SECRET", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

    settings = Settings()
    with pytest.raises(
        RuntimeError,
        match="AGENT_API_KEY must be configured with a non-default value of at least 32 characters in production",
    ):
        settings.validate_runtime_configuration()


@pytest.mark.parametrize("insecure_value", ["too-short", None, "", "change-me", "CHANGE_ME", "replace-me"])
def test_production_rejects_insecure_or_short_auth_token_secret(monkeypatch, insecure_value):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AGENT_API_KEY", "a" * 32)
    if insecure_value is None:
        monkeypatch.delenv("AUTH_TOKEN_SECRET", raising=False)
    else:
        monkeypatch.setenv("AUTH_TOKEN_SECRET", insecure_value)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

    settings = Settings()
    with pytest.raises(
        RuntimeError,
        match="AUTH_TOKEN_SECRET must be configured with a non-default value of at least 32 characters in production",
    ):
        settings.validate_runtime_configuration()


def test_production_accepts_valid_secrets_32_chars_or_more(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AGENT_API_KEY", "a" * 32)
    monkeypatch.setenv("AUTH_TOKEN_SECRET", "b" * 64)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

    settings = Settings()
    settings.validate_runtime_configuration()


def test_non_production_allows_short_or_missing_secrets(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("AGENT_API_KEY", raising=False)
    monkeypatch.delenv("AUTH_TOKEN_SECRET", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings()
    settings.validate_runtime_configuration()
