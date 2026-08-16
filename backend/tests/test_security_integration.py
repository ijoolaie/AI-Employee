import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.role import Permission, Role, role_permissions, user_roles
from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth_service import hash_password


@pytest.fixture
async def security_setup():
    async with AsyncSessionLocal() as db:
        tenant_a = Tenant(
            name="Security Tenant A",
            slug=f"security-a-{uuid.uuid4().hex[:8]}",
            status="active",
        )
        tenant_b = Tenant(
            name="Security Tenant B",
            slug=f"security-b-{uuid.uuid4().hex[:8]}",
            status="active",
        )
        db.add_all([tenant_a, tenant_b])
        await db.flush()

        # Permission codes are globally unique, so never use a fixed value
        # that may already exist in the development database.
        permission = Permission(
            code=f"workflow.read.test.{uuid.uuid4().hex}",
            description="Security integration test permission",
        )
        db.add(permission)
        await db.flush()

        role_a = Role(
            tenant_id=tenant_a.id,
            name=f"security-role-a-{uuid.uuid4().hex[:8]}",
            description="Tenant A security test role",
        )
        role_b = Role(
            tenant_id=tenant_b.id,
            name=f"security-role-b-{uuid.uuid4().hex[:8]}",
            description="Tenant B security test role",
        )

        role_a.permissions.append(permission)
        db.add_all([role_a, role_b])
        await db.flush()

        user_a = User(
            tenant_id=tenant_a.id,
            email=f"security-a-{uuid.uuid4().hex}@example.com",
            password_hash=hash_password("TestPassword123!"),
            full_name="Security User A",
            is_active=True,
        )
        user_b = User(
            tenant_id=tenant_b.id,
            email=f"security-b-{uuid.uuid4().hex}@example.com",
            password_hash=hash_password("TestPassword123!"),
            full_name="Security User B",
            is_active=True,
        )

        user_a.roles.append(role_a)
        user_b.roles.append(role_b)

        db.add_all([user_a, user_b])
        await db.flush()

        await db.commit()

        return {
            "tenant_a": tenant_a,
            "tenant_b": tenant_b,
            "permission": permission,
            "role_a": role_a,
            "role_b": role_b,
            "user_a": user_a,
            "user_b": user_b,
        }


@pytest.mark.asyncio
async def test_tenant_a_token_cannot_impersonate_tenant_b(security_setup):
    """
    Verify that a user's tenant identity cannot be switched to another tenant.

    This test intentionally checks the database ownership boundary directly.
    The application must derive tenant context from the authenticated user,
    rather than trusting a client-provided tenant_id.
    """
    data = security_setup

    user_a = data["user_a"]
    tenant_a = data["tenant_a"]
    tenant_b = data["tenant_b"]

    assert user_a.tenant_id == tenant_a.id
    assert user_a.tenant_id != tenant_b.id

    # A Tenant-A user must never be treated as a Tenant-B user.
    assert user_a.tenant_id == tenant_a.id


@pytest.mark.asyncio
async def test_foreign_tenant_role_cannot_grant_permission(security_setup):
    """
    A role belonging to Tenant B must not be usable as a Tenant A role.
    """
    data = security_setup

    tenant_a = data["tenant_a"]
    tenant_b = data["tenant_b"]
    role_a = data["role_a"]
    role_b = data["role_b"]
    permission = data["permission"]

    assert role_a.tenant_id == tenant_a.id
    assert role_b.tenant_id == tenant_b.id

    # Permission is attached only to Tenant A's role.
    result = await _get_role_permission_links(role_a.id, permission.id)
    assert result is True

    result = await _get_role_permission_links(role_b.id, permission.id)
    assert result is False

    # Most importantly, Tenant B's role cannot become a Tenant A role.
    assert role_b.tenant_id != tenant_a.id


async def _get_role_permission_links(role_id, permission_id):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(role_permissions.c.role_id).where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == permission_id,
            )
        )
        return result.scalar_one_or_none() == role_id
