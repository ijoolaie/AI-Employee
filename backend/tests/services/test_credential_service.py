from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.models.credential import Credential
from app.services import credential_service


@pytest.mark.asyncio
async def test_store_credential_encrypts_secret_and_returns_opaque_ref(monkeypatch):
    tenant_id = uuid4(); captured = {}
    class Db:
        def add(self, obj): captured["credential"] = obj
        async def flush(self): return None
    async def _audit(*args, **kwargs): return None
    monkeypatch.setattr(credential_service.audit_service, "record", _audit)
    credential = await credential_service.store_credential(Db(), tenant_id=tenant_id, provider="shopify", name="shopify:access_token", secret="super-secret")
    assert credential.ciphertext != "super-secret"
    assert credential_service.credential_ref(credential) == f"cred:{credential.id}"


@pytest.mark.asyncio
async def test_resolve_credential_locks_row_against_concurrent_revoke():
    credential = Credential(id=uuid4(), tenant_id=uuid4(), provider="x", name="x", ciphertext="bad", status="revoked", active=False)
    captured = {}
    class Result:
        def scalar_one_or_none(self): return credential
    class Db:
        async def execute(self, statement):
            captured["statement"] = statement
            return Result()
    with pytest.raises(ValidationAppError, match="revoked"):
        await credential_service.resolve_credential(Db(), tenant_id=credential.tenant_id, credential_id=credential.id)
    assert getattr(captured["statement"], "_for_update_arg", None) is not None


@pytest.mark.asyncio
async def test_resolve_credential_rejects_revoked_credential():
    credential = Credential(id=uuid4(), tenant_id=uuid4(), provider="x", name="x", ciphertext="bad", status="revoked", active=False)
    class Result:
        def scalar_one_or_none(self): return credential
    class Db:
        async def execute(self, statement): return Result()
    with pytest.raises(ValidationAppError, match="revoked"):
        await credential_service.resolve_credential(Db(), tenant_id=credential.tenant_id, credential_id=credential.id)


@pytest.mark.asyncio
async def test_resolve_credential_rejects_expired_credential():
    credential = Credential(id=uuid4(), tenant_id=uuid4(), provider="x", name="x", ciphertext="bad", status="active", active=True, expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    class Result:
        def scalar_one_or_none(self): return credential
    class Db:
        async def execute(self, statement): return Result()
    with pytest.raises(ValidationAppError, match="expired"):
        await credential_service.resolve_credential(Db(), tenant_id=credential.tenant_id, credential_id=credential.id)


@pytest.mark.asyncio
async def test_agent_credential_access_requires_policy(monkeypatch):
    tenant_id, agent_id, run_id, credential_id = uuid4(), uuid4(), uuid4(), uuid4()
    credential = Credential(id=credential_id, tenant_id=tenant_id, provider="shopify", name="token", ciphertext="bad", status="active", active=True)
    class Result:
        def scalar_one_or_none(self): return credential
    class Db:
        async def execute(self, statement): return Result()
    monkeypatch.setattr(credential_service, "current_agent_execution_context", lambda: (tenant_id, agent_id, run_id, None, None))
    async def _deny(*args, **kwargs): raise ValidationAppError("permission denied")
    monkeypatch.setattr(credential_service, "assert_authorized", _deny)
    with pytest.raises(ValidationAppError, match="permission denied"):
        await credential_service.resolve_credential(Db(), tenant_id=tenant_id, credential_id=credential_id, agent_instance_id=agent_id, run_id=run_id)


@pytest.mark.asyncio
async def test_shopify_legacy_plaintext_access_token_is_rejected():
    from app.services import shopify_service
    integration = SimpleNamespace(tenant_id=uuid4(), config={"shop_domain": "example.myshopify.com", "access_token": "legacy-secret"})
    class Db: pass
    with pytest.raises(ValidationAppError, match="credential reference"):
        await shopify_service._cfg(Db(), integration)
