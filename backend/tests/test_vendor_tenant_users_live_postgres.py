"""Disposable-PostgreSQL HTTP acceptance for Vendor subtree user lifecycle."""

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


def _disposable_database_url() -> str:
    url = os.environ.get("LIFECYCLE_TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("Requires the isolated disposable PostgreSQL 16 lifecycle database")
    parsed = make_url(url)
    if (
        parsed is None
        or parsed.drivername != "postgresql+asyncpg"
        or parsed.host not in {"127.0.0.1", "localhost"}
        or parsed.port != 15436
        or parsed.username != "aiep"
        or parsed.password != "aiep"
        or parsed.database != "ai_employee_lifecycle_test"
    ):
        raise RuntimeError("Vendor lifecycle acceptance requires the isolated disposable PostgreSQL 16 database on loopback:15436.")
    return url


@pytest.mark.asyncio
async def test_vendor_subtree_user_lifecycle_over_http(monkeypatch):
    db_url = _disposable_database_url()
    from app.core.config import get_settings
    from app.core.database import get_db
    from app.core.security import create_access_token
    from app.main import app
    from app.models.audit_log import AuditLog
    from app.models.role import Permission, Role
    from app.models.tenant import Tenant
    from app.models.tenant_demo_grant import TenantDemoGrant
    from app.models.tenant_invitation import TenantInvitation
    from app.models.user import User
    from app.services import audit_service

    monkeypatch.setattr(get_settings(), "rate_limit_enabled", False)
    engine = create_async_engine(db_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    run_id = uuid.uuid4().hex
    vendor = Tenant(name=f"Vendor lifecycle {run_id}", slug=f"vendor-life-{run_id}", status="active", tenant_kind="vendor", settings={})
    reseller = Tenant(name=f"Reseller lifecycle {run_id}", slug=f"reseller-life-{run_id}", status="active", tenant_kind="reseller", access_grant_required=True, settings={})
    reseller.parent = vendor
    nested_customer = Tenant(name=f"Nested customer {run_id}", slug=f"nested-customer-{run_id}", status="active", tenant_kind="customer", access_grant_required=True, settings={})
    nested_customer.parent = reseller
    foreign_vendor = Tenant(name=f"Foreign vendor {run_id}", slug=f"foreign-vendor-{run_id}", status="active", tenant_kind="vendor", settings={})
    foreign_reseller = Tenant(name=f"Foreign reseller {run_id}", slug=f"foreign-reseller-{run_id}", status="active", tenant_kind="reseller", settings={})
    foreign_reseller.parent = foreign_vendor

    missing = object()
    previous_override = app.dependency_overrides.get(get_db, missing)
    try:
        async with sessions() as session:
            session.add_all([vendor, reseller, nested_customer, foreign_vendor, foreign_reseller])
            await session.flush()
            codes = (
                "vendor.reseller.read", "vendor.reseller.manage",
                "vendor.customer.read", "vendor.customer.manage", "employee.read",
            )
            permissions = {row.code: row for row in (await session.execute(select(Permission).where(Permission.code.in_(codes)))).scalars()}
            for code in codes:
                if code not in permissions:
                    permissions[code] = Permission(code=code, description=f"Vendor lifecycle test {code}")
                    session.add(permissions[code])
            await session.flush()
            vendor_admin_role = Role(tenant_id=vendor.id, name="Admin", description="Vendor lifecycle test administrator", permissions=[permissions[code] for code in codes])
            target_admin_role = Role(tenant_id=reseller.id, name="Admin", description="Target tenant administrator")
            target_member_role = Role(tenant_id=reseller.id, name="Member", description="Target tenant member", permissions=[permissions["employee.read"]])
            actor = User(tenant_id=vendor.id, email=f"vendor-actor-{run_id}@example.com", password_hash="not-used", full_name="Vendor Actor", is_active=True, is_superuser=False, is_platform_admin=False, roles=[vendor_admin_role])
            admins = [User(tenant_id=reseller.id, email=f"target-admin-{i}-{run_id}@example.com", password_hash="not-used", full_name=f"Target Admin {i}", is_active=True, is_superuser=False, is_platform_admin=False, roles=[target_admin_role]) for i in range(2)]
            member = User(tenant_id=reseller.id, email=f"target-member-{run_id}@example.com", password_hash="not-used", full_name="Target Member", is_active=False, is_superuser=False, is_platform_admin=False, roles=[])
            session.add_all([vendor_admin_role, target_admin_role, target_member_role, actor, *admins, member])
            await session.flush()
            grant = TenantDemoGrant(tenant_id=reseller.id, granted_by_user_id=actor.id, reason="Isolated Vendor user lifecycle acceptance", expires_at=datetime.now(timezone.utc) + timedelta(days=1))
            accepted = TenantInvitation(tenant_id=reseller.id, user_id=member.id, email=member.email, token_hash=uuid.uuid4().hex + uuid.uuid4().hex, expires_at=datetime.now(timezone.utc) + timedelta(days=1), accepted_at=datetime.now(timezone.utc))
            session.add_all([grant, accepted])
            await session.commit()

        async def override_get_db() -> AsyncIterator[AsyncSession]:
            async with sessions() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_db] = override_get_db
        token = create_access_token(subject=actor.id, tenant_id=vendor.id, extra_claims={"auth_token_version": actor.auth_token_version})
        headers = {"Authorization": f"Bearer {token}"}
        base = f"/api/v1/edition/vendor/tenants/{reseller.id}/users"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            listed = await client.get(base, headers=headers)
            assert listed.status_code == 200, listed.text
            assert {row["email"] for row in listed.json()["data"]} == {admins[0].email, admins[1].email, member.email}
            nested = await client.get(f"/api/v1/edition/vendor/tenants/{nested_customer.id}/users", headers=headers)
            assert nested.status_code == 200, nested.text
            foreign = await client.get(f"/api/v1/edition/vendor/tenants/{foreign_reseller.id}/users", headers=headers)
            assert foreign.status_code == 403, foreign.text

            invite = await client.post(f"{base}/invitations", headers=headers, json={"email": f"new-invite-{run_id}@example.com", "full_name": "Invited User"})
            assert invite.status_code == 201, invite.text
            invite_data = invite.json()["data"]
            async with sessions() as session:
                stored = (await session.execute(select(TenantInvitation).where(TenantInvitation.id == invite_data["id"]))).scalar_one()
                assert stored.token_hash != invite_data["token"]
                assert invite_data["token"] not in stored.token_hash
            revoked = await client.post(f"{base}/invitations/{invite_data['id']}/revoke", headers=headers)
            assert revoked.status_code == 200, revoked.text

            activated = await client.post(f"{base}/{member.id}/status", headers=headers, json={"is_active": True})
            assert activated.status_code == 200, activated.text
            deactivated = await client.post(f"{base}/{member.id}/status", headers=headers, json={"is_active": False})
            assert deactivated.status_code == 200, deactivated.text
            assigned = await client.post(f"{base}/{member.id}/roles", headers=headers, json={"role_ids": [str(target_member_role.id)]})
            assert assigned.status_code == 200, assigned.text
            demoted = await client.post(f"{base}/{admins[0].id}/roles", headers=headers, json={"role_ids": []})
            assert demoted.status_code == 200, demoted.text
            last_admin = await client.post(f"{base}/{admins[1].id}/status", headers=headers, json={"is_active": False})
            assert last_admin.status_code == 409, last_admin.text

        async with sessions() as session:
            refreshed = (await session.execute(select(User).where(User.id == member.id))).scalar_one()
            assert refreshed.tenant_id == reseller.id
            assert refreshed.is_active is False
            actions_target = set((await session.execute(select(AuditLog.action).where(AuditLog.tenant_id == reseller.id))).scalars())
            actions_vendor = set((await session.execute(select(AuditLog.action).where(AuditLog.tenant_id == vendor.id))).scalars())
            assert {"vendor_user.invitation_created", "tenant.invitation_revoked", "vendor_user.status_updated", "vendor_user.roles_updated"}.issubset(actions_target)
            assert {"vendor.reseller.invitation_created", "vendor.reseller.invitation_revoked", "vendor.reseller.status_updated", "vendor.reseller.roles_updated"}.issubset(actions_vendor)
            assert (await audit_service.verify_ledger(session, tenant_id=reseller.id))["valid"] is True
            assert (await audit_service.verify_ledger(session, tenant_id=vendor.id))["valid"] is True
    finally:
        if previous_override is missing:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override
        await engine.dispose()
