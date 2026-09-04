from app.core.privacy import REDACTED, redact_sensitive_data


def test_redacts_credentials_and_direct_pii_recursively():
    source = {
        "user_email": "alice@example.com",
        "password": "not-for-logs",
        "nested": {
            "API-Key": "secret-value",
            "safe_id": "work-item-123",
            "items": [{"phone_number": "+1-555-0100", "count": 2}],
        },
    }

    redacted = redact_sensitive_data(source)

    assert redacted["user_email"] == REDACTED
    assert redacted["password"] == REDACTED
    assert redacted["nested"]["API-Key"] == REDACTED
    assert redacted["nested"]["safe_id"] == "work-item-123"
    assert redacted["nested"]["items"][0]["phone_number"] == REDACTED
    assert source["password"] == "not-for-logs"


def test_preserves_non_mapping_scalars_and_tuple_shape():
    value = ("ok", {"client_secret": "hidden", "attempt": 3})
    assert redact_sensitive_data(value) == ("ok", {"client_secret": REDACTED, "attempt": 3})
