from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4
import pytest
from app.services import customer_channel_service

class Result:
    def __init__(self, value=None, rows=None): self.value, self.rows = value, rows
    def scalar_one_or_none(self): return self.value
    def scalars(self): return self
    def all(self): return self.rows

class DB:
    def __init__(self, *results): self.results, self.calls = list(results), 0
    async def execute(self, _statement):
        self.calls += 1
        return self.results[self.calls - 1]
    async def flush(self): pass

def fixtures(attempts=0, expires_at=None, email="buyer@example.com"):
    tenant, cid = uuid4(), uuid4()
    conv = SimpleNamespace(id=cid, tenant_id=tenant, customer_email="buyer@example.com",
                           email_verified_at=None, verified_email=None, customer_id=None)
    challenge = SimpleNamespace(id=uuid4(), tenant_id=tenant, conversation_id=cid,
        email=email, code_hash="expected", attempts=attempts,
        expires_at=expires_at or datetime.now(timezone.utc)+timedelta(minutes=5),
        consumed_at=None)
    return conv, challenge

def patch(monkeypatch, conv, digest="expected"):
    async def get_conv(*a, **kw): return conv
    monkeypatch.setattr(customer_channel_service, "_get_conversation", get_conv)
    monkeypatch.setattr(customer_channel_service, "_verification_code_hash", lambda **kw: digest)

@pytest.mark.asyncio
@pytest.mark.parametrize("attempts,expiry", [
    (0, datetime.now(timezone.utc)-timedelta(seconds=1)),
    (5, datetime.now(timezone.utc)+timedelta(minutes=5)),
])
async def test_expired_or_exhausted_challenge_fails_closed(monkeypatch, attempts, expiry):
    conv, challenge = fixtures(attempts, expiry)
    db = DB(Result(challenge)); patch(monkeypatch, conv)
    assert await customer_channel_service.verify_customer_email(
        db, conversation_id=conv.id, token="token", code="123456"
    ) is False
    assert db.calls == 1 and conv.email_verified_at is None

@pytest.mark.asyncio
async def test_invalid_code_consumes_attempt(monkeypatch):
    conv, challenge = fixtures()
    db = DB(Result(challenge)); patch(monkeypatch, conv, "wrong")
    assert await customer_channel_service.verify_customer_email(
        db, conversation_id=conv.id, token="token", code="000000"
    ) is False
    assert challenge.attempts == 1 and conv.email_verified_at is None

@pytest.mark.asyncio
async def test_changed_email_invalidates_challenge(monkeypatch):
    conv, challenge = fixtures(email="old@example.com")
    db = DB(Result(challenge)); patch(monkeypatch, conv)
    assert await customer_channel_service.verify_customer_email(
        db, conversation_id=conv.id, token="token", code="123456"
    ) is False
    assert challenge.attempts == 0 and conv.email_verified_at is None

@pytest.mark.asyncio
async def test_duplicate_customer_email_does_not_auto_link(monkeypatch):
    conv, challenge = fixtures()
    rows = [SimpleNamespace(id=uuid4()), SimpleNamespace(id=uuid4())]
    db = DB(Result(challenge), Result(rows=rows)); patch(monkeypatch, conv)
    assert await customer_channel_service.verify_customer_email(
        db, conversation_id=conv.id, token="token", code="123456"
    ) is True
    assert conv.verified_email == "buyer@example.com"
    assert conv.email_verified_at is not None and conv.customer_id is None
    assert db.calls == 2
