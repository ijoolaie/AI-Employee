import hashlib
import hmac
from datetime import datetime, timezone

from app.services.workflow_trigger_service import evaluate_condition, next_cron_time, verify_signature


def test_condition_operators():
    ctx = {"input": {"amount": 15, "tags": ["vip", "book"]}}
    assert evaluate_condition({"path": "$.input.amount", "operator": "gte", "value": 15}, ctx)
    assert evaluate_condition({"path": "$.input.tags", "operator": "contains", "value": "vip"}, ctx)
    assert evaluate_condition({"path": "$.input.missing", "operator": "exists"}, ctx) is False


def test_cron_next_time():
    start = datetime(2026, 8, 7, 10, 24, 30, tzinfo=timezone.utc)
    assert next_cron_time("*/5 * * * *", start).minute == 25


def test_webhook_signature():
    secret = "test-secret"
    payload = b'{"message":"hello"}'
    sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_signature(secret, payload, sig)
    assert not verify_signature(secret, payload, sig + "0")
