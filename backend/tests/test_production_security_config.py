"""Production configuration fail-closed security regression tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _production_env(**overrides):
    values = {
        "app_env": "production",
        "debug": False,
        "secret_key": "x" * 64,
        "rate_limit_enabled": True,
        "rate_limit_fail_closed": True,
        "cors_origins": ["https://app.example.com"],
        "frontend_base_url": "https://app.example.com",
        "frontend_app_url": "https://app.example.com",
        "database_url": "postgresql+asyncpg://prod:strong-password@db.internal:5432/aiep",
        "database_url_sync": "postgresql://prod:strong-password@db.internal:5432/aiep",
        "redis_url": "redis://:strong-password@redis.internal:6379/0",
        "celery_broker_url": "redis://:strong-password@redis.internal:6379/1",
        "celery_result_backend": "redis://:strong-password@redis.internal:6379/2",
        "lm_studio_base_url": "https://ai.example.com/v1",
    }
    values.update(overrides)
    return values


def test_secure_production_configuration_is_accepted():
    settings = Settings(**_production_env())
    assert settings.app_env == "production"
    assert settings.debug is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("debug", True),
        ("rate_limit_enabled", False),
        ("rate_limit_fail_closed", False),
        ("secret_key", "short"),
        ("frontend_base_url", "http://app.example.com"),
        ("frontend_app_url", "http://app.example.com"),
        ("cors_origins", ["http://app.example.com"]),
        ("database_url", "postgresql+asyncpg://prod:pw@localhost:5432/aiep"),
        ("redis_url", "redis://:pw@127.0.0.1:6379/0"),
        ("database_url", "postgresql+asyncpg://aiep:aiep@db.internal:5432/aiep"),
        ("lm_studio_base_url", "http://ai.example.com/v1"),
    ],
)
def test_unsafe_production_configuration_fails_closed(field, value):
    with pytest.raises((ValueError, ValidationError)):
        Settings(**_production_env(**{field: value}))
