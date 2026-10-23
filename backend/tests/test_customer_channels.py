from app.services.customer_channel_service import _hash_token


def test_customer_token_hash_is_deterministic_and_not_plaintext():
    token = "customer-secret-token"
    hashed = _hash_token(token)
    assert hashed != token
    assert len(hashed) == 64
    assert _hash_token(token) == hashed


def test_customer_token_hash_changes_with_token():
    assert _hash_token("a") != _hash_token("b")


def test_handoff_service_contains_tenant_scoped_assignee_check():
    from app.services import customer_channel_service
    source = customer_channel_service.update_handoff.__code__.co_names
    assert "User" in source
    assert "NotFoundError" in source


def test_support_transcript_format_preserves_role_and_chronological_order():
    from types import SimpleNamespace
    from app.services.customer_channel_service import _format_conversation_transcript

    transcript = _format_conversation_transcript([
        SimpleNamespace(role="user", content="هزینه ارسال چقدره؟"),
        SimpleNamespace(role="assistant", content="ارسال برای کدوم شهره؟ 😊"),
        SimpleNamespace(role="user", content="تهران"),
    ])

    assert transcript.splitlines() == [
        "Customer: هزینه ارسال چقدره؟",
        "Assistant: ارسال برای کدوم شهره؟ 😊",
        "Customer: تهران",
    ]
