from datetime import datetime, timezone
import uuid

from app.core.security import encrypt_secret, decrypt_secret
from app.models.outbox import OutboxMessage


def test_secret_round_trip():
    value = "super-secret-" + uuid.uuid4().hex
    encrypted = encrypt_secret(value)
    assert encrypted != value
    assert decrypt_secret(encrypted) == value


def test_outbox_defaults_are_durable():
    message = OutboxMessage(kind="workflow.execute", payload={"workflow_run_id": str(uuid.uuid4())})
    assert message.status == "pending"
    assert message.attempts == 0
