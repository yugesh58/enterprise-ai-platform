import pytest
from pydantic import ValidationError

from app.core.config import Settings


VALID_PRODUCTION_CONFIG = {
    "APP_DATABASE_USER": "app_runtime_user",
    "APP_DATABASE_PASSWORD": "c" * 40,
    "SQL_AGENT_DATABASE_USER": "sql_agent_user",
    "SQL_AGENT_DATABASE_PASSWORD": "e" * 40,

    "ENVIRONMENT": "production",
    "DEBUG": False,
    "API_AUTH_ENABLED": True,
    "API_KEY": "a" * 40,
    "RATE_LIMIT_ENABLED": True,
    "RATE_LIMIT_KEY_SECRET": "b" * 40,
    "QDRANT_API_KEY": "c" * 40,
    "REDIS_PASSWORD": "d" * 40,
    "MEMORY_PROVIDER": "redis",
}


def test_valid_production_security_config():
    settings = Settings(
        _env_file=None,
        **VALID_PRODUCTION_CONFIG,
    )

    assert settings.ENVIRONMENT == "production"
    assert settings.DEBUG is False


@pytest.mark.parametrize(
    ("overrides", "error_message"),
    [
        (
            {"DEBUG": True},
            "DEBUG must be disabled",
        ),
        (
            {"API_AUTH_ENABLED": False},
            "API authentication must be enabled",
        ),
        (
            {"API_KEY": "short"},
            "API_KEY must contain at least 32 characters",
        ),
        (
            {"RATE_LIMIT_ENABLED": False},
            "Rate limiting must be enabled",
        ),
        (
            {"RATE_LIMIT_KEY_SECRET": "short"},
            "RATE_LIMIT_KEY_SECRET must contain",
        ),
        (
            {"RATE_LIMIT_KEY_SECRET": "a" * 40},
            "must be different",
        ),
        (
            {"SQL_AGENT_DATABASE_USER": ""},
            "SQL_AGENT_DATABASE_USER",
        ),
        (
            {"SQL_AGENT_DATABASE_PASSWORD": "short"},
            "SQL_AGENT_DATABASE_PASSWORD must contain",
        ),
        (
            {"SQL_AGENT_DATABASE_USER": "app_runtime_user"},
            "SQL Agent must use a dedicated database user",
        ),
    ],
)
def test_invalid_production_security_config(
    overrides,
    error_message,
):
    config = {
        **VALID_PRODUCTION_CONFIG,
        **overrides,
    }

    with pytest.raises(ValidationError, match=error_message):
        Settings(_env_file=None, **config)


def test_development_allows_short_api_key():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="development",
        API_KEY="local-dev-key",
    )

    assert settings.API_KEY == "local-dev-key"


def test_sql_agent_url_uses_explicit_credentials_without_changing_other_urls():
    settings = Settings(
        _env_file=None,
        DATABASE_HOST="sql-host",
        DATABASE_PORT=5544,
        DATABASE_NAME="sample_db",
        DATABASE_USER="legacy_user",
        DATABASE_PASSWORD="legacy-password",
        SQL_AGENT_DATABASE_USER="sql_agent",
        SQL_AGENT_DATABASE_PASSWORD="new-password",
        APP_DATABASE_USER="app_runtime",
        APP_DATABASE_PASSWORD="app-password",
        DOCUMENT_DATABASE_USER="document_user",
        DOCUMENT_DATABASE_PASSWORD="document-password",
    )

    assert "sql_agent:new-password@sql-host:5544/sample_db" in (
        settings.SQL_AGENT_DATABASE_URL
    )
    assert "legacy_user:legacy-password" in settings.DATABASE_URL
    assert "app_runtime:app-password" in settings.APP_DATABASE_URL
    assert "document_user:document-password" in (
        settings.DOCUMENT_DATABASE_URL
    )


def test_development_sql_agent_url_falls_back_to_legacy_credentials():
    settings = Settings(
        _env_file=None,
        DATABASE_USER="legacy_sql_agent",
        DATABASE_PASSWORD="legacy-password",
    )

    assert "legacy_sql_agent:legacy-password" in (
        settings.SQL_AGENT_DATABASE_URL
    )


def test_non_development_sql_agent_url_requires_explicit_credentials():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="staging",
        DATABASE_USER="legacy_sql_agent",
        DATABASE_PASSWORD="legacy-password",
    )

    with pytest.raises(
        ValueError,
        match="explicitly configured outside development",
    ):
        settings.SQL_AGENT_DATABASE_URL


def test_sql_agent_url_rejects_partially_configured_credentials():
    settings = Settings(
        _env_file=None,
        SQL_AGENT_DATABASE_USER="sql_agent",
    )

    with pytest.raises(ValueError, match="must be set together"):
        settings.SQL_AGENT_DATABASE_URL
@pytest.mark.parametrize("size", [0, -1, -10])
def test_upload_size_must_be_positive(size):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            MAX_UPLOAD_SIZE_MB=size,
        )