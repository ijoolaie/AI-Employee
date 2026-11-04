"""Real PostgreSQL + HTTP API test for commercial edition token boundaries."""
import os
import uuid
from collections.abc import AsyncIterator
import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from httpx import ASGITransport, AsyncClient

def _test_database_url() -> str:
    url = os.environ.get("SUPPORT_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("Test database URL is required; refusing to run.")
    parsed = make_url(url)
    if (parsed.drivername != "postgresql+asyncpg" or parsed.username not in {"support_test_user", "aiep"}
        or parsed.host not in {"127.0.0.1", "localhost"} or parsed.port not in {5432, 15433}
        or parsed.database != "support_test" or not parsed.password):
        raise RuntimeError("URL must target the dedicated local support_test database; refusing to run.")
    return url

@pytest.mark.asyncio
async def test_vendor_reseller_customer_tokens_are_scoped_to_their_edition(monkeypatch):
    db_url = _test_database_url()
    from app.core.database import get_db
    from app.core.security import create_access_token, hash_password
    from app.main import app
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.role import Permission, Role, role_permissions, user_roles
    engine = create_async_engine(db_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    run_id = uuid.uuid4().hex
    vendor = Tenant(name=f"API test vendor {run_id}", slug=f"api-vendor-{run_id}", status="active", tenant_kind="vendor", vendor_release_tag="vendor-release-test", delivery_revision="delivery-test", settings={})
    reseller = Tenant(name=f"API test reseller {run_id}", slug=f"api-reseller-{run_id}", status="active", tenant_kind="reseller", settings={})
    customer = Tenant(name=f"API test customer {run_id}", slug=f"api-customer-{run_id}", status="active", tenant_kind="customer", settings={})
    reseller.parent = vendor
    customer.parent = reseller
    users = []
    try:
        async with sessions() as session:
            session.add_all([vendor, reseller, customer])
            await session.flush()
            permission_codes = ("vendor.reseller.read", "reseller.customer.read")
            permission_by_code = {
                permission.code: permission
                for permission in (
                    await session.execute(
                        select(Permission).where(Permission.code.in_(permission_codes))
                    )
                ).scalars()
            }
            for code, description in (
                ("vendor.reseller.read", "Read own direct resellers"),
                ("reseller.customer.read", "Read own direct customers"),
            ):
                if code not in permission_by_code:
                    permission = Permission(code=code, description=description)
                    session.add(permission)
                    permission_by_code[code] = permission
            for tenant, kind in ((vendor, "vendor"), (reseller, "reseller"), (customer, "customer")):
                user = User(tenant_id=tenant.id, email=f"{kind}-{run_id}@example.com", password_hash=hash_password("Local-Test-Password-2026!"), full_name=kind.title(), is_active=True, is_superuser=False, is_platform_admin=False)
                role = Role(tenant_id=tenant.id, name="Admin", description="integration test tenant admin")
                if kind == "vendor":
                    role.permissions = [permission_by_code["vendor.reseller.read"]]
                elif kind == "reseller":
                    role.permissions = [permission_by_code["reseller.customer.read"]]
                user.roles = [role]
                session.add_all([user, role])
                users.append((tenant, user))
            await session.commit()
        async def override_get_db() -> AsyncIterator:
            async with sessions() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        from types import SimpleNamespace
        from app.services import auth_service
        monkeypatch.setattr(auth_service, "get_settings", lambda: SimpleNamespace(default_vendor_tenant_slug=vendor.slug))
        missing = object()
        previous = app.dependency_overrides.get(get_db, missing)
        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                tokens = {}
                for tenant, user in users:
                    token = create_access_token(subject=user.id, tenant_id=tenant.id, extra_claims={"auth_token_version": user.auth_token_version})
                    headers = {"Authorization": f"Bearer {token}"}
                    me = await client.get("/api/v1/auth/me", headers=headers)
                    assert me.status_code == 200, me.text
                    assert me.json()["data"]["tenant"]["tenant_kind"] == tenant.tenant_kind
                    tokens[tenant.tenant_kind] = headers
                    # Exercise the real password-login route, not only a hand-issued JWT.
                    login_response = await client.post("/api/v1/auth/login", json={
                        "tenant_slug": tenant.slug,
                        "email": user.email,
                        "password": "Local-Test-Password-2026!",
                    })
                    assert login_response.status_code == 200, login_response.text
                    login_token = login_response.json()["data"]["access_token"]
                    login_me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {login_token}"})
                    assert login_me.status_code == 200, login_me.text
                    assert login_me.json()["data"]["tenant"]["tenant_kind"] == tenant.tenant_kind
                    assert login_me.json()["data"]["user"]["is_platform_admin"] is False
                checks = [("vendor", "/api/v1/edition/vendor/resellers", 200), ("vendor", "/api/v1/edition/reseller/customers", 403), ("reseller", "/api/v1/edition/vendor/resellers", 403), ("reseller", "/api/v1/edition/reseller/customers", 200), ("customer", "/api/v1/edition/vendor/resellers", 403), ("customer", "/api/v1/edition/reseller/customers", 403)]
                for kind, path, expected in checks:
                    response = await client.get(path, headers=tokens[kind])
                    assert response.status_code == expected, f"{kind} -> {path}: expected {expected}, got {response.status_code}: {response.text}"

                # Verify the real public registration endpoint cannot create a platform admin.
                registration = {
                    "tenant_name": f"Registration test {run_id}",
                    "tenant_slug": f"registration-{run_id}",
                    "email": f"register-{run_id}@example.com",
                    "password": "Local-Registration-2026!",
                    "full_name": "Registration Test",
                }
                registered = await client.post("/api/v1/auth/register", json=registration)
                assert registered.status_code == 202, registered.text
                registered_tenant_id = registered.json()["data"]["tenant_id"]
                assert "approved payment" in registered.json()["data"]["message"]
                login_response = await client.post("/api/v1/auth/login", json={"email": registration["email"], "password": registration["password"], "tenant_slug": registration["tenant_slug"]})
                assert login_response.status_code == 200, login_response.text
                registered_token = login_response.json()["data"]["access_token"]
                auth_headers = {"Authorization": f"Bearer {registered_token}"}
                registered_me = await client.get("/api/v1/auth/me", headers=auth_headers)
                assert registered_me.status_code == 200, registered_me.text
                assert registered_me.json()["data"]["tenant"]["access_granted"] is False
                pending_subscription = await client.get("/api/v1/billing/subscription", headers=auth_headers)
                assert pending_subscription.status_code == 200, pending_subscription.text
                assert pending_subscription.json()["data"]["status"] == "incomplete"
                assert pending_subscription.json()["data"]["trial_ends_at"] is None
                denied_employees = await client.get("/api/v1/employees", headers=auth_headers)
                assert denied_employees.status_code == 402, denied_employees.text
                async with sessions() as session:
                    registered_user = (await session.execute(select(User).where(User.email == registration["email"], User.tenant_id == registered_tenant_id))).scalar_one()
                    assert registered_user.is_active is True
                    assert registered_user.is_superuser is False
                    assert registered_user.is_platform_admin is False
                    registered_tenant = (await session.execute(select(Tenant).where(Tenant.id == registered_user.tenant_id))).scalar_one()
                    assert registered_tenant.access_grant_required is True
                    assert registered_tenant.parent_tenant_id == vendor.id
                    assert registered_tenant.vendor_release_tag == vendor.vendor_release_tag
                    assert registered_tenant.delivery_revision == vendor.delivery_revision
                    registered_role_id = (await session.execute(select(user_roles.c.role_id).where(user_roles.c.user_id == registered_user.id))).scalar_one()
                    registered_grants = set((await session.execute(select(Permission.code).join(role_permissions, role_permissions.c.permission_id == Permission.id).where(role_permissions.c.role_id == registered_role_id))).scalars())
                    assert "billing.manage" in registered_grants
                    assert "employee.read" in registered_grants
                    assert "support.escalation.create" in registered_grants
                    assert "skill_marketplace.purchase" in registered_grants
                    assert "marketplace.install" in registered_grants
                    assert "employee_marketplace.publish" in registered_grants
                    assert "employee_marketplace.install" in registered_grants
                    assert "employee_marketplace.revoke" in registered_grants
        finally:
            if previous is missing:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
    finally:
        await engine.dispose()