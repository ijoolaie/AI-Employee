"""Privacy helpers for security-sensitive structured metadata.

Audit and log metadata is for operational reconstruction, not payload storage.
This module provides a small, deterministic boundary that removes common
credential and direct-identifier fields before structured metadata crosses
into durable audit storage or JSON logging.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "secret_key",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "set_cookie",
        "client_secret",
        "webhook_secret",
        "stripe_secret_key",
        "stripe_webhook_secret",
        "smtp_password",
        "database_url",
        "database_url_sync",
        "redis_url",
        "celery_broker_url",
        "celery_result_backend",
    }
)

PII_KEYS = frozenset(
    {
        "email",
        "user_email",
        "phone",
        "phone_number",
        "address",
        "street_address",
        "customer_name",
        "full_name",
    }
)

REDACTED = "[REDACTED]"


def _key_class(key: object) -> str | None:
    normalized = str(key).strip().lower().replace("-", "_")
    if normalized in SENSITIVE_KEYS:
        return "secret"
    if normalized in PII_KEYS:
        return "pii"
    return None


def redact_sensitive_data(value: Any) -> Any:
    """Recursively redact credentials and direct PII from structured values.

    Mapping keys are matched case-insensitively after normalizing ``-`` to
    ``_``. Lists/tuples are traversed while scalar values remain unchanged.
    This function never mutates caller-owned containers.
    """
    if isinstance(value, Mapping):
        return {
            key: REDACTED if _key_class(key) else redact_sensitive_data(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive_data(item) for item in value)
    return value
