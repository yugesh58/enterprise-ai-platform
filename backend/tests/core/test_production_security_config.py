import pytest
from pydantic import ValidationError

from app.core.config import Settings


VALID_PRODUCTION_CONFIG = {
    "ENVIRONMENT": "production",
    "DEBUG": False,
    "API_AUTH_ENABLED": True,
    "API_KEY": "a" * 40,
    "RATE_LIMIT_ENABLED": True,
    "RATE_LIMIT_KEY_SECRET": "b" * 40,
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
@pytest.mark.parametrize("size", [0, -1, -10])
def test_upload_size_must_be_positive(size):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            MAX_UPLOAD_SIZE_MB=size,
        )