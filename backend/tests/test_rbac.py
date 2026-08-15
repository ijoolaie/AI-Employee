"""Core RBAC and tenant-isolation unit tests.

These tests are intentionally dependency-light: endpoint integration tests can
run against PostgreSQL in CI, while these checks protect the authorization
contract without requiring infrastructure.
"""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.deps import TenantContext, has_permission


@pytest.mark.asyncio
async def test_permission_is_granted_only_from_current_tenant_role():
    tenant_id = uuid4()
    other_tenant_id = uuid4()

    allowed = SimpleNamespace(code="employee.read")
    denied = SimpleNamespace(code="run.execute")

    current_role = SimpleNamespace(
        tenant_id=tenant_id,
        permissions=[allowed],
    )
    foreign_role = SimpleNamespace(
        tenant_id=other_tenant_id,
        permissions=[denied],
    )
    user = SimpleNamespace(
        id=uuid4(),
        is_superuser=False,
        roles=[current_role, foreign_role],
    )
    tenant = SimpleNamespace(id=tenant_id)
    ctx = TenantContext(user=user, tenant=tenant)

    assert await has_permission(ctx, "employee.read")
    assert not await has_permission(ctx, "run.execute")


@pytest.mark.asyncio
async def test_superuser_compatibility_path_has_full_core_access():
    user = SimpleNamespace(id=uuid4(), is_superuser=True, roles=[])
    tenant = SimpleNamespace(id=uuid4())
    ctx = TenantContext(user=user, tenant=tenant)

    assert await has_permission(ctx, "employee.write")
    assert await has_permission(ctx, "run.execute")


@pytest.mark.asyncio
async def test_foreign_tenant_role_cannot_grant_permission():
    tenant_id = uuid4()
    foreign_role = SimpleNamespace(
        tenant_id=uuid4(),
        permissions=[SimpleNamespace(code="file.write")],
    )
    user = SimpleNamespace(
        id=uuid4(),
        is_superuser=False,
        roles=[foreign_role],
    )
    ctx = TenantContext(user=user, tenant=SimpleNamespace(id=tenant_id))

    assert not await has_permission(ctx, "file.write")
