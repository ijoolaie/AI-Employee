"""Safety validation for persisted Test Center evidence payloads."""

from __future__ import annotations

from typing import Any

_SENSITIVE_KEY_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "access_key",
    "authorization",
    "cookie",
    "credential",
)
_MAX_DEPTH = 8
_MAX_ITEMS = 500


def sanitize_test_payload(value: Any, *, _depth: int = 0, _seen: set[int] | None = None) -> Any:
    """Validate a JSON-like payload and reject sensitive fields."""
    if _depth > _MAX_DEPTH:
        raise ValueError("test evidence nesting is too deep")
    seen = _seen if _seen is not None else set()
    if isinstance(value, dict):
        if len(value) > _MAX_ITEMS:
            raise ValueError("test evidence contains too many fields")
        marker = id(value)
        if marker in seen:
            raise ValueError("cyclic test evidence is forbidden")
        seen.add(marker)
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
                raise ValueError("secret-bearing test evidence is forbidden")
            result[str(key)] = sanitize_test_payload(item, _depth=_depth + 1, _seen=seen)
        seen.remove(marker)
        return result
    if isinstance(value, list):
        if len(value) > _MAX_ITEMS:
            raise ValueError("test evidence contains too many items")
        return [sanitize_test_payload(item, _depth=_depth + 1, _seen=seen) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise ValueError("test evidence must contain only JSON-compatible values")
