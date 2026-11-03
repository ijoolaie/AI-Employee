import hashlib
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.deps import has_permission
from app.services.api_key_service import KEY_PREFIX


def test_api_key_prefix_and_digest_are_non_reversible_contract():
    secret = KEY_PREFIX + "example-secret"
    digest = hashlib.sha256(secret.encode()).hexdigest()
    assert secret.startswith("aiep_live_")
    assert len(digest) == 64
    assert secret not in digest


@pytest.mark.asyncio
async def test_scoped_api_key_cannot_exceed_key_scopes():
    tenant_id = uuid4()
    permission = SimpleNamespace(code="run.read")
    role = SimpleNamespace(tenant_id=tenant_id, permissions=[permission])
    user = SimpleNamespace(is_superuser=False, roles=[role])
    ctx = SimpleNamespace(
        user=user,
        tenant_id=tenant_id,
        tenant=SimpleNamespace(id=tenant_id),
        api_key_scopes=["run.read"],
    )

    assert await has_permission(ctx, "run.read") is True
    assert await has_permission(ctx, "run.execute") is False


@pytest.mark.asyncio
async def test_scoped_api_key_cannot_grant_permission_owner_does_not_have():
    tenant_id = uuid4()
    permission = SimpleNamespace(code="run.read")
    role = SimpleNamespace(tenant_id=tenant_id, permissions=[permission])
    user = SimpleNamespace(is_superuser=False, roles=[role])
    ctx = SimpleNamespace(
        user=user,
        tenant_id=tenant_id,
        tenant=SimpleNamespace(id=tenant_id),
        api_key_scopes=["run.execute"],
    )

    assert await has_permission(ctx, "run.execute") is False


def test_superuser_flag_cannot_delegate_unheld_api_key_permissions():
    from app.api.v1.api_keys import _assert_api_key_scopes_within_authority
    from fastapi import HTTPException

    tenant_id = uuid4()
    ctx = SimpleNamespace(
        tenant_id=tenant_id,
        user=SimpleNamespace(
            is_superuser=True,
            roles=[SimpleNamespace(tenant_id=tenant_id, name="Admin", permissions=[])],
        ),
    )
    with pytest.raises(HTTPException) as exc:
        _assert_api_key_scopes_within_authority(ctx, {"run.execute"}, set())
    assert exc.value.status_code == 403


def test_superuser_flag_cannot_delegate_edition_scopes_without_admin_role():
    from app.api.v1.api_keys import _assert_api_key_scopes_within_authority
    from fastapi import HTTPException

    tenant_id = uuid4()
    ctx = SimpleNamespace(
        tenant_id=tenant_id,
        user=SimpleNamespace(is_superuser=True, roles=[]),
    )
    with pytest.raises(HTTPException) as exc:
        _assert_api_key_scopes_within_authority(
            ctx, {"edition.vendor.tenants.read"}, {"edition.vendor.tenants.read"}
        )
    assert exc.value.status_code == 403
