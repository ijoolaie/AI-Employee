from app.services.customer_channel_service import _hash_token


def test_customer_token_hash_is_deterministic_and_not_plaintext():
    token = "customer-secret-token"
    hashed = _hash_token(token)
    assert hashed != token
    assert len(hashed) == 64
    assert _hash_token(token) == hashed


def test_customer_token_hash_changes_with_token():
    assert _hash_token("a") != _hash_token("b")
