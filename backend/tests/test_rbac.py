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
async def test_superuser_without_explicit_tenant_role_has_no_core_permissions():
    user = SimpleNamespace(id=uuid4(), is_superuser=True, roles=[])
    tenant = SimpleNamespace(id=uuid4())
    ctx = TenantContext(user=user, tenant=tenant)

    assert not await has_permission(ctx, "employee.write")
    assert not await has_permission(ctx, "run.execute")


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



def test_default_tenant_admin_has_skill_marketplace_permissions():
    from app.services.auth_service import DEFAULT_TENANT_ADMIN_PERMISSIONS

    assert "skill_marketplace.publish" in DEFAULT_TENANT_ADMIN_PERMISSIONS
    assert "skill_marketplace.read" in DEFAULT_TENANT_ADMIN_PERMISSIONS


def test_worker_tool_permissions_ignore_superuser_flag_and_foreign_roles():
    from app.services.run_service import _effective_run_tool_permissions

    tenant_id = uuid4()
    local_role = SimpleNamespace(
        tenant_id=tenant_id,
        permissions=[SimpleNamespace(code="run.execute")],
    )
    foreign_role = SimpleNamespace(
        tenant_id=uuid4(),
        permissions=[SimpleNamespace(code="privacy.customer.delete")],
    )
    user = SimpleNamespace(is_superuser=True, roles=[local_role, foreign_role])

    assert _effective_run_tool_permissions(user, tenant_id) == {"run.execute"}
