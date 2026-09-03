import pytest

from app.core.test_center_safety import sanitize_test_payload


@pytest.mark.parametrize(
    "key",
    ["password", "api_token", "client_secret", "authorization", "cookie", "credential"],
)
def test_rejects_sensitive_keys(key):
    with pytest.raises(ValueError, match="secret-bearing"):
        sanitize_test_payload({"nested": [{key: "hidden"}]})


def test_preserves_nested_safe_payload():
    payload = {"checks": [{"name": "health", "passed": True}], "count": 1}
    assert sanitize_test_payload(payload) == payload


def test_rejects_excessive_nesting():
    payload = value = {}
    for _ in range(10):
        value["next"] = {}
        value = value["next"]
    with pytest.raises(ValueError, match="nesting"):
        sanitize_test_payload(payload)


def test_rejects_non_json_values():
    with pytest.raises(ValueError, match="JSON-compatible"):
        sanitize_test_payload({"value": object()})
