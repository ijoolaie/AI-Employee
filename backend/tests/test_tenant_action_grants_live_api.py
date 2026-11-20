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

@pytest.mark.asyncio
async def test_vendor_reseller_and_reseller_customer_action_grant_symmetry():
    """Exercise both delegated action-grant APIs and their tenant/user ceilings on PostgreSQL."""
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
    vendor = Tenant(name=f"Symmetry vendor {run_id}", slug=f"sym-vendor-{run_id}", status="active", tenant_kind="vendor", settings={})
    reseller = Tenant(name=f"Symmetry reseller {run_id}", slug=f"sym-reseller-{run_id}", status="active", tenant_kind="reseller", settings={}, parent=vendor)
    outsider = Tenant(name=f"Symmetry outsider {run_id}", slug=f"sym-outsider-{run_id}", status="active", tenant_kind="customer", settings={}, parent=reseller)
    try:
        async with sessions() as session:
            session.add_all([vendor, reseller, outsider])
            await session.flush()

            async def make_user(tenant, label):
                user = User(
                    tenant_id=tenant.id,
                    email=f"{label}-{run_id}@example.com",
                    password_hash="not-used",
                    full_name=label,
                    is_active=True,
                    is_superuser=False,
                    is_platform_admin=False,
                    roles=[],
                )
                session.add(user)
                await session.flush()
                return user

            vendor_grantor = await make_user(vendor, "Vendor Grantor")
            vendor_delegate = await make_user(vendor, "Vendor Delegate")
            reseller_grantor = await make_user(reseller, "Reseller Grantor")
            reseller_delegate = await make_user(reseller, "Reseller Delegate")
            outsider_user = await make_user(outsider, "Outsider User")

            async def permission(code):
                row = (await session.execute(select(Permission).where(Permission.code == code))).scalar_one_or_none()
                if row is None:
                    row = Permission(code=code, description=f"Action grant acceptance: {code}")
                    session.add(row)
                    await session.flush()
                return row

            vendor_role = Role(tenant_id=vendor.id, name="Admin", description="Vendor action grant test")
            vendor_role.permissions = [await permission("vendor.reseller.create")]
            vendor_grantor.roles = [vendor_role]
            reseller_role = Role(tenant_id=reseller.id, name="Admin", description="Reseller action grant test")
            reseller_role.permissions = [await permission("reseller.customer.create")]
            reseller_grantor.roles = [reseller_role]
            session.add_all([vendor_role, reseller_role])
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
            def headers(user):
                token = create_access_token(
                    subject=user.id,
                    tenant_id=user.tenant_id,
                    extra_claims={"auth_token_version": user.auth_token_version},
                )
                return {"Authorization": f"Bearer {token}"}

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                vendor_payload = {
                    "user_id": str(vendor_delegate.id),
                    "action_code": "vendor.reseller.create",
                    "reason": "Symmetric Vendor-to-Reseller delegation acceptance",
                    "expires_in_days": 30,
                }
                vendor_created = await client.post("/api/v1/edition/vendor/action-grants", headers=headers(vendor_grantor), json=vendor_payload)
                assert vendor_created.status_code == 201, vendor_created.text
                vendor_grant_id = vendor_created.json()["data"]["id"]

                vendor_cross_tenant_target = await client.post(
                    "/api/v1/edition/vendor/action-grants",
                    headers=headers(vendor_grantor),
                    json={**vendor_payload, "user_id": str(outsider_user.id)},
                )
                assert vendor_cross_tenant_target.status_code == 404, vendor_cross_tenant_target.text

                vendor_unauthorized_grantor = await client.post(
                    "/api/v1/edition/vendor/action-grants",
                    headers=headers(vendor_delegate),
                    json={**vendor_payload, "user_id": str(vendor_grantor.id)},
                )
                assert vendor_unauthorized_grantor.status_code == 403, vendor_unauthorized_grantor.text

                vendor_revoked = await client.delete(
                    f"/api/v1/edition/vendor/action-grants/{vendor_grant_id}",
                    headers=headers(vendor_grantor),
                )
                assert vendor_revoked.status_code == 200, vendor_revoked.text

                reseller_payload = {
                    "user_id": str(reseller_delegate.id),
                    "action_code": "reseller.customer.create",
                    "reason": "Symmetric Reseller-to-Customer delegation acceptance",
                    "expires_in_days": 30,
                }
                reseller_created = await client.post("/api/v1/edition/reseller/action-grants", headers=headers(reseller_grantor), json=reseller_payload)
                assert reseller_created.status_code == 201, reseller_created.text
                reseller_grant_id = reseller_created.json()["data"]["id"]

                reseller_cross_tenant_target = await client.post(
                    "/api/v1/edition/reseller/action-grants",
                    headers=headers(reseller_grantor),
                    json={**reseller_payload, "user_id": str(outsider_user.id)},
                )
                assert reseller_cross_tenant_target.status_code == 404, reseller_cross_tenant_target.text

                reseller_unauthorized_grantor = await client.post(
                    "/api/v1/edition/reseller/action-grants",
                    headers=headers(reseller_delegate),
                    json={**reseller_payload, "user_id": str(reseller_grantor.id)},
                )
                assert reseller_unauthorized_grantor.status_code == 403, reseller_unauthorized_grantor.text

                reseller_revoked = await client.delete(
                    f"/api/v1/edition/reseller/action-grants/{reseller_grant_id}",
                    headers=headers(reseller_grantor),
                )
                assert reseller_revoked.status_code == 200, reseller_revoked.text

            async with sessions() as session:
                vendor_grant = (await session.execute(select(TenantActionGrant).where(TenantActionGrant.id == vendor_grant_id))).scalar_one()
                reseller_grant = (await session.execute(select(TenantActionGrant).where(TenantActionGrant.id == reseller_grant_id))).scalar_one()
                assert vendor_grant.revoked_at is not None
                assert reseller_grant.revoked_at is not None
                assert vendor_grant.tenant_id == vendor.id
                assert reseller_grant.tenant_id == reseller.id
        finally:
            if previous is missing:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
    finally:
        await engine.dispose()
