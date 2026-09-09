import base64
import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services import shopify_oauth_state


class _FakeResult:
    def __init__(self, rowcount: int):
        self.rowcount = rowcount


class _FakeDB:
    def __init__(self, rowcounts):
        self.rowcounts = iter(rowcounts)
        self.added = []

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        return None

    async def execute(self, statement):
        return _FakeResult(next(self.rowcounts))


def _settings(monkeypatch):
    monkeypatch.setattr(shopify_oauth_state, "get_settings", lambda: SimpleNamespace(secret_key="test-secret"))


def _state(tenant_id: uuid.UUID, shop: str, timestamp: int, nonce: str = "nonce") -> str:
    raw = f"{tenant_id}:{shop}:{timestamp}:{nonce}"
    signature = hmac.new(b"test-secret", raw.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{raw}:{signature}".encode()).decode()


def test_parse_state_is_bound_to_shop(monkeypatch):
    _settings(monkeypatch)
    tenant_id = uuid.uuid4()
    state = _state(tenant_id, "example.myshopify.com", int(datetime.now(timezone.utc).timestamp()))

    parsed_tenant, shop = shopify_oauth_state._parse(state)

    assert parsed_tenant == tenant_id
    assert shop == "example.myshopify.com"


@pytest.mark.asyncio
async def test_consume_state_allows_only_matching_shop(monkeypatch):
    _settings(monkeypatch)
    tenant_id = uuid.uuid4()
    state = _state(tenant_id, "example.myshopify.com", int(datetime.now(timezone.utc).timestamp()))
    db = _FakeDB([1])

    with pytest.raises(Exception, match="shop mismatch"):
        await shopify_oauth_state.consume_state(db, state, "other.myshopify.com")

    assert db.rowcounts


@pytest.mark.asyncio
async def test_consume_state_rejects_replay_when_atomic_update_affects_zero_rows(monkeypatch):
    _settings(monkeypatch)
    tenant_id = uuid.uuid4()
    state = _state(tenant_id, "example.myshopify.com", int(datetime.now(timezone.utc).timestamp()))
    db = _FakeDB([1, 0])

    assert await shopify_oauth_state.consume_state(db, state, "example.myshopify.com") == tenant_id
    with pytest.raises(Exception, match="already used"):
        await shopify_oauth_state.consume_state(db, state, "example.myshopify.com")


@pytest.mark.asyncio
async def test_issue_state_persists_hashed_one_time_record(monkeypatch):
    _settings(monkeypatch)
    tenant_id = uuid.uuid4()
    db = _FakeDB([])

    state = await shopify_oauth_state.issue_state(db, tenant_id, "https://Example.myshopify.com/")

    assert len(db.added) == 1
    row = db.added[0]
    assert row.tenant_id == tenant_id
    assert row.shop_domain == "example.myshopify.com"
    assert row.state_hash == hashlib.sha256(state.encode()).hexdigest()
    assert row.used_at is None
