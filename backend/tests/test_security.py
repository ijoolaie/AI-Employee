"""Unit tests for security helpers."""

from uuid import uuid4

from app.core.security import hash_password, verify_password, create_access_token, decode_token


def test_password_hash_and_verify():
    hashed = hash_password("Secret123!")
    assert hashed != "Secret123!"
    assert verify_password("Secret123!", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip():
    token = create_access_token(subject="user-1", tenant_id="tenant-1")
    payload = decode_token(token)
    assert payload["sub"] == "user-1"
    assert payload["tenant_id"] == "tenant-1"
    assert payload["type"] == "access"


def test_access_token_normalizes_uuid_identity_claims():
    user_id, tenant_id = uuid4(), uuid4()
    token = create_access_token(subject=user_id, tenant_id=tenant_id)
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)


def test_timer_exposes_elapsed_before_context_exit():
    import time
    from app.core.logging import Timer

    with Timer() as timer:
        # Keep the assertion independent of OS scheduler/timer resolution.
        time.sleep(0.001)
        live = timer.elapsed_ms
        assert live > 0

    assert timer.duration_ms >= live
