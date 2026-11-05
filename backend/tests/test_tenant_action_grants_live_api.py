"""PostgreSQL-backed acceptance for user-bound edition action grants."""

import os
import uuid
from collections.abc import AsyncIterator

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
async def test_user_action_grant_enables_scoped_provisioning_and_revocation():
    db_url = _dedicated_test_database_url()
    from app.core.database import get_db
    from app.core.security import create_access_token
    from app.main import app
    from app.models.role import Permission, Role
    from app.models.tenant import Tenant
    from app.models.tenant_action_grant import TenantActionGrant
    from app.models.user import User

    engine = create_async_engine(db_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    run_id = uuid.uuid4().hex
    vendor = Tenant(
        name=f"Action grant vendor {run_id}",
        slug=f"action-grant-vendor-{run_id}",
        status="active",
        tenant_kind="vendor",
        settings={},
    )
    try:
        async with sessions() as session:
            session.add(vendor)
            await session.flush()
            grantor = User(
                tenant_id=vendor.id,
                email=f"action-grantor-{run_id}@example.com",
                password_hash="not-used",
                full_name="Action Grantor",
                is_active=True,
                is_superuser=False,
                is_platform_admin=False,
                roles=[],
            )
            actor = User(
                tenant_id=vendor.id,
                email=f"action-actor-{run_id}@example.com",
                password_hash="not-used",
                full_name="Action Actor",
                is_active=True,
                is_superuser=False,
                is_platform_admin=False,
                roles=[],
            )
            session.add_all([grantor, actor])
            await session.flush()
            permission = (await session.execute(
                select(Permission).where(Permission.code == "vendor.customer.create")
            )).scalar_one_or_none()
            if permission is None:
                permission = Permission(code="vendor.customer.create", description="Create direct Vendor customers")
                session.add(permission)
                await session.flush()
            admin_role = Role(tenant_id=vendor.id, name="Admin", description="Action grant test admin")
            admin_role.permissions = [permission]
            grantor.roles = [admin_role]
            session.add(admin_role)
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
                subject=grantor.id,
                tenant_id=vendor.id,
                extra_claims={"auth_token_version": grantor.auth_token_version},
            )
            actor_token = create_access_token(
                subject=actor.id,
                tenant_id=vendor.id,
                extra_claims={"auth_token_version": actor.auth_token_version},
            )
            grantor_headers = {"Authorization": f"Bearer {grantor_token}"}
            actor_headers = {"Authorization": f"Bearer {actor_token}"}
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                payload = {
                    "user_id": str(actor.id),
                    "action_code": "vendor.customer.create",
                    "reason": "Allow this member to provision direct customer tenants",
                    "expires_in_days": 30,
                }
                created = await client.post(
                    "/api/v1/edition/vendor/action-grants",
                    headers=grantor_headers,
                    json=payload,
                )
                assert created.status_code == 201, created.text
                grant_id = created.json()["data"]["id"]

                escalation = await client.post(
                    "/api/v1/edition/vendor/action-grants",
                    headers=grantor_headers,
                    json={**payload, "action_code": "vendor.reseller.create"},
                )
                assert escalation.status_code == 403, escalation.text

                child_payload = {
                    "name": f"Action Grant Customer {run_id}",
                    "slug": f"action-grant-customer-{run_id}",
                    "admin_email": f"child-admin-{run_id}@example.com",
                    "full_name": "Child Admin",
                }
                wrong_action = await client.post(
                    "/api/v1/edition/vendor/resellers",
                    headers=actor_headers,
                    json=child_payload,
                )
                assert wrong_action.status_code == 403, wrong_action.text

                provisioned = await client.post(
                    "/api/v1/edition/vendor/customers",
                    headers=actor_headers,
                    json=child_payload,
                )
                assert provisioned.status_code == 201, provisioned.text

                revoked = await client.delete(
                    f"/api/v1/edition/vendor/action-grants/{grant_id}",
                    headers=grantor_headers,
                )
                assert revoked.status_code == 200, revoked.text

                denied_after_revoke = await client.post(
                    "/api/v1/edition/vendor/customers",
                    headers=actor_headers,
                    json={**child_payload, "slug": f"action-grant-revoked-{run_id}"},
                )
                assert denied_after_revoke.status_code == 403, denied_after_revoke.text

                async with sessions() as session:
                    grant = (await session.execute(
                        select(TenantActionGrant).where(TenantActionGrant.id == grant_id)
                    )).scalar_one()
                    assert grant.revoked_at is not None
        finally:
            if previous is missing:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
    finally:
        await engine.dispose()
