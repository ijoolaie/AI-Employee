"""PostgreSQL acceptance test for operator-controlled default Vendor bootstrap."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def _support_test_database_url() -> str:
    from os import environ

    url = environ.get("SUPPORT_TEST_DATABASE_URL", "")
    if not url:
        raise RuntimeError("SUPPORT_TEST_DATABASE_URL is required; refusing to run.")
    parsed = make_url(url)
    if (
        parsed.drivername != "postgresql+asyncpg"
        or parsed.username not in {"support_test_user", "aiep"}
        or parsed.host not in {"127.0.0.1", "localhost"}
        or parsed.port not in {5432, 15433}
        or parsed.database != "support_test"
        or not parsed.password
    ):
        raise RuntimeError("URL must target the dedicated local support_test database; refusing to run.")
    return url


@pytest.mark.asyncio
async def test_default_vendor_bootstrap_is_idempotent_and_least_privilege(monkeypatch):
    from types import SimpleNamespace

    from app.models.audit_log import AuditLog
    from app.models.role import Permission, Role, role_permissions, user_roles
    from app.models.tenant import Tenant
    from app.models.user import User
    from scripts import bootstrap_default_vendor

    run_id = uuid.uuid4().hex
    slug = f"bootstrap-vendor-{run_id}"
    email = f"bootstrap-{run_id}@example.com"
    engine = create_async_engine(_support_test_database_url(), poolclass=NullPool)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    monkeypatch.setattr(bootstrap_default_vendor, "get_settings", lambda: SimpleNamespace(default_vendor_tenant_slug=slug))
    monkeypatch.setattr(bootstrap_default_vendor, "AsyncSessionLocal", sessions)
    monkeypatch.setenv("DEFAULT_VENDOR_BOOTSTRAP_TENANT_NAME", f"Bootstrap Vendor {run_id}")
    monkeypatch.setenv("DEFAULT_VENDOR_BOOTSTRAP_ADMIN_EMAIL", email)
    monkeypatch.setenv("DEFAULT_VENDOR_BOOTSTRAP_ADMIN_PASSWORD", "Bootstrap-Test-Password-2026!")

    tenant_id = None
    try:
        await bootstrap_default_vendor.bootstrap()
        await bootstrap_default_vendor.bootstrap()

        async with sessions() as db:
            vendor = (await db.execute(select(Tenant).where(Tenant.slug == slug))).scalar_one()
            tenant_id = vendor.id
            user = (await db.execute(select(User).where(User.tenant_id == vendor.id, User.email == email))).scalar_one()
            role = (await db.execute(select(Role).where(Role.tenant_id == vendor.id, Role.name == "Admin"))).scalar_one()
            await db.refresh(role, attribute_names=["permissions"])
            grants = {permission.code for permission in role.permissions}

            assert vendor.tenant_kind == "vendor"
            assert vendor.parent_tenant_id is None
            assert vendor.status == "active"
            assert user.is_active is True
            assert user.is_superuser is False
            assert user.is_platform_admin is False
            assigned_user_ids = set((await db.execute(select(user_roles.c.user_id).where(user_roles.c.role_id == role.id))).scalars())
            assert user.id in assigned_user_ids
            assert set(bootstrap_default_vendor.VENDOR_ADMIN_PERMISSIONS) <= grants
            assert len(grants) == len(bootstrap_default_vendor.VENDOR_ADMIN_PERMISSIONS)
    finally:
        if tenant_id is not None:
            async with sessions() as db:
                await db.execute(delete(AuditLog).where(AuditLog.tenant_id == tenant_id))
                await db.execute(delete(user_roles).where(user_roles.c.user_id.in_(select(User.id).where(User.tenant_id == tenant_id))))
                await db.execute(delete(role_permissions).where(role_permissions.c.role_id.in_(select(Role.id).where(Role.tenant_id == tenant_id))))
                await db.execute(delete(User).where(User.tenant_id == tenant_id))
                await db.execute(delete(Role).where(Role.tenant_id == tenant_id))
                await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
                await db.commit()
        await engine.dispose()