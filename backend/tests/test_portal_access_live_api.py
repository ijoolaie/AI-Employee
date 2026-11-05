"""PostgreSQL-backed portal grant, context, and immediate revocation contract."""

import os
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def _dedicated_test_database_url() -> str:
    url = os.environ.get("SUPPORT_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("Test database URL is required; refusing to run.")
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
async def test_portal_grant_activates_context_and_revocation_invalidates_it(monkeypatch):
    db_url = _dedicated_test_database_url()
    from app.core.database import get_db
    from app.core.security import create_access_token
    from app.main import app
    from app.models.portal_access_grant import PortalAccessGrant
    from app.models.role import Permission, Role
    from app.models.tenant import Tenant
    from app.models.tenant_demo_grant import TenantDemoGrant
    from app.models.user import User

    engine = create_async_engine(db_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    run_id = uuid.uuid4().hex
    vendor = Tenant(name=f"Portal test vendor {run_id}", slug=f"portal-vendor-{run_id}", status="active", tenant_kind="vendor", settings={})
    target = Tenant(name=f"Portal test reseller {run_id}", slug=f"portal-reseller-{run_id}", status="active", tenant_kind="reseller", access_grant_required=True, settings={})
    target.parent = vendor
    try:
        async with sessions() as session:
            session.add_all([vendor, target])
            await session.flush()
            grantor = User(
                tenant_id=vendor.id, email=f"portal-grantor-{run_id}@example.com",
                password_hash="not-used", full_name="Portal Grantor", is_active=True,
                is_superuser=False, is_platform_admin=False,
            )
            actor = User(
                tenant_id=vendor.id, email=f"portal-actor-{run_id}@example.com",
                password_hash="not-used", full_name="Portal Actor", is_active=True,
                is_superuser=False, is_platform_admin=False,
            )
            session.add_all([grantor, actor])
            await session.flush()
            permission = (await session.execute(
                select(Permission).where(Permission.code == "employee.read")
            )).scalar_one_or_none()
            if permission is None:
                permission = Permission(code="employee.read", description="Read employees")
                session.add(permission)
                await session.flush()
            admin_role = Role(tenant_id=vendor.id, name="Admin", description="Portal integration admin")
            reader_role = Role(tenant_id=vendor.id, name="Employee Reader", description="Portal integration reader")
            reader_role.permissions = [permission]
            grantor.roles = [admin_role]
            actor.roles = [reader_role]
            session.add_all([
                admin_role,
                reader_role,
                TenantDemoGrant(
                    tenant_id=target.id,
                    granted_by_user_id=grantor.id,
                    reason="Isolated portal context integration test",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                ),
            ])
            await session.commit()

        async def override_get_db() -> AsyncIterator[AsyncSession]:
            async with sessions() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        missing = object()
        previous = app.dependency_overrides.get(get_db, missing)
        app.dependency_overrides[get_db] = override_get_db
        try:
            grantor_token = create_access_token(
                subject=grantor.id, tenant_id=vendor.id,
                extra_claims={"auth_token_version": grantor.auth_token_version},
            )
            actor_token = create_access_token(
                subject=actor.id, tenant_id=vendor.id,
                extra_claims={"auth_token_version": actor.auth_token_version},
            )
            grantor_headers = {"Authorization": f"Bearer {grantor_token}"}
            actor_headers = {"Authorization": f"Bearer {actor_token}"}
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                created = await client.post(
                    "/api/v1/edition/vendor/portal-access-grants",
                    headers=grantor_headers,
                    json={
                        "actor_user_id": str(actor.id),
                        "target_tenant_id": str(target.id),
                        "reason": "Support the directly owned reseller",
                    },
                )
                assert created.status_code == 201, created.text
                grant_id = created.json()["data"]["id"]

                activated = await client.post(
                    f"/api/v1/edition/vendor/portal-access-grants/{grant_id}/activate",
                    headers=actor_headers,
                )
                assert activated.status_code == 200, activated.text
                portal_token = activated.json()["data"]["access_token"]
                portal_headers = {"Authorization": f"Bearer {portal_token}"}

                me = await client.get("/api/v1/auth/me", headers=portal_headers)
                assert me.status_code == 200, me.text
                assert me.json()["data"]["tenant"]["id"] == str(target.id)
                assert me.json()["data"]["user"]["tenant_id"] == str(vendor.id)
                assert "employee.read" in me.json()["data"]["user"]["permissions"]

                employees = await client.get("/api/v1/employees", headers=portal_headers)
                assert employees.status_code == 200, employees.text
                blocked_admin = await client.get("/api/v1/tenant-admin/users", headers=portal_headers)
                assert blocked_admin.status_code == 403, blocked_admin.text
                blocked_billing = await client.get("/api/v1/billing/subscription", headers=portal_headers)
                assert blocked_billing.status_code == 403, blocked_billing.text

                revoked = await client.delete(
                    f"/api/v1/edition/vendor/portal-access-grants/{grant_id}",
                    headers=grantor_headers,
                )
                assert revoked.status_code == 200, revoked.text
                denied = await client.get("/api/v1/auth/me", headers=portal_headers)
                assert denied.status_code == 403, denied.text

                async with sessions() as session:
                    grant = (await session.execute(
                        select(PortalAccessGrant).where(PortalAccessGrant.id == grant_id)
                    )).scalar_one()
                    assert grant.revoked_at is not None
        finally:
            if previous is missing:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
    finally:
        await engine.dispose()
