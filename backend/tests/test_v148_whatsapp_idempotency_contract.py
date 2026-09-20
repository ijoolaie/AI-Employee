from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_v148_whatsapp_idempotency_contract():
    model = (ROOT / "app/models/conversation.py").read_text()
    webhook = (ROOT / "app/api/v1/channel_webhooks.py").read_text()
    migration = next((ROOT / "alembic/versions").glob("v148_whatsapp_idempotency.py")).read_text()

    assert "external_conversation_key" in model
    assert "provider_message_id" in model
    assert "uq_customer_conversations_external_key" in migration
    assert "uq_customer_messages_provider_id" in migration
    assert 'provider_message_id=message.get("message_id") or None' in webhook
    assert "execute_run_task.delay(str(run.id), str(channel.tenant_id))" in webhook


def test_v148_does_not_make_public_conversations_unique():
    migration = (ROOT / "alembic/versions/v148_whatsapp_idempotency.py").read_text()

    assert "customer_conversations" in migration
    assert "channel_id" in migration
    assert "external_conversation_key" in migration
    assert "customer_phone" not in migration
