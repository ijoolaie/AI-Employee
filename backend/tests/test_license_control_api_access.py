"""Live API acceptance for commercial license ownership and tenant boundaries."""
import os
import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def _test_database_url() -> str:
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
async def test_license_issue_list_revoke_and_issuer_isolation():
    db_url = _test_database_url()
    from app.core.database import get_db
    from app.core.security import create_access_token, hash_password
    from app.main import app
    from app.models.role import Role
    from app.models.tenant import Tenant
    from app.models.user import User

    engine = create_async_engine(db_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    run_id = uuid.uuid4().hex
    vendor = Tenant(name=f"License vendor {run_id}", slug=f"license-vendor-{run_id}", status="active", tenant_kind="vendor", settings={})
    reseller = Tenant(name=f"License reseller {run_id}", slug=f"license-reseller-{run_id}", status="active", tenant_kind="reseller", settings={})
    customer = Tenant(name=f"License customer {run_id}", slug=f"license-customer-{run_id}", status="active", tenant_kind="customer", settings={})
    outsider = Tenant(name=f"License outsider {run_id}", slug=f"license-outsider-{run_id}", status="active", tenant_kind="reseller", settings={})
    reseller.parent = vendor
    customer.parent = reseller
    users = []
    try:
        async with sessions() as session:
            session.add_all([vendor, reseller, customer, outsider])
            await session.flush()
            for tenant, kind in ((vendor, "vendor"), (reseller, "reseller"), (customer, "customer"), (outsider, "outsider")):
                user = User(
                    tenant_id=tenant.id,
                    email=f"{kind}-{run_id}@example.com",
                    password_hash=hash_password("Local-Test-Password-2026!"),
                    full_name=kind.title(),
                    is_active=True,
                    is_superuser=False,
                    is_platform_admin=False,
                )
                role = Role(tenant_id=tenant.id, name="Admin", description="license API integration test")
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

        missing = object()
        previous = app.dependency_overrides.get(get_db, missing)
        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = {}
                for tenant, user in users:
                    token = create_access_token(
                        subject=user.id,
                        tenant_id=tenant.id,
                        extra_claims={"auth_token_version": user.auth_token_version},
                    )
                    headers[tenant.tenant_kind if tenant.tenant_kind != "reseller" or tenant is reseller else "outsider"] = {
                        "Authorization": f"Bearer {token}"
                    }

                issue_vendor = await client.post(
                    f"/api/v1/edition/licenses/vendor/resellers/{reseller.id}",
                    headers=headers["vendor"],
                    json={"expires_in_days": 90, "feature_codes": ["workflow_runs"], "metadata": {"source": "test"}},
                )
                assert issue_vendor.status_code == 201, issue_vendor.text
                vendor_license = issue_vendor.json()["data"]
                assert vendor_license["issuer_tenant_id"] == str(vendor.id)
                assert vendor_license["tenant_id"] == str(reseller.id)
                assert vendor_license["license_key"]

                issue_reseller = await client.post(
                    f"/api/v1/edition/licenses/reseller/customers/{customer.id}",
                    headers=headers["reseller"],
                    json={"expires_in_days": 30, "feature_codes": ["knowledge_search"]},
                )
                assert issue_reseller.status_code == 201, issue_reseller.text
                reseller_license = issue_reseller.json()["data"]
                assert reseller_license["issuer_tenant_id"] == str(reseller.id)
                assert reseller_license["tenant_id"] == str(customer.id)

                # List responses are scoped to issuer and never disclose bearer keys.
                vendor_list = await client.get("/api/v1/edition/licenses/vendor", headers=headers["vendor"])
                assert vendor_list.status_code == 200, vendor_list.text
                vendor_rows = vendor_list.json()["data"]
                assert any(row["id"] == vendor_license["id"] for row in vendor_rows)
                assert all("license_key" not in row for row in vendor_rows)
                assert all(row["issuer_tenant_id"] == str(vendor.id) for row in vendor_rows)

                reseller_list = await client.get("/api/v1/edition/licenses/reseller", headers=headers["reseller"])
                assert reseller_list.status_code == 200, reseller_list.text
                reseller_rows = reseller_list.json()["data"]
                assert any(row["id"] == reseller_license["id"] for row in reseller_rows)
                assert all("license_key" not in row for row in reseller_rows)
                assert all(row["issuer_tenant_id"] == str(reseller.id) for row in reseller_rows)
                assert all(row["id"] != vendor_license["id"] for row in reseller_rows)

                customer_list = await client.get("/api/v1/edition/licenses/reseller", headers=headers["customer"])
                assert customer_list.status_code == 403, customer_list.text

                outsider_list = await client.get("/api/v1/edition/licenses/reseller", headers=headers["outsider"])
                assert outsider_list.status_code == 200, outsider_list.text
                assert all(row["issuer_tenant_id"] == str(outsider.id) for row in outsider_list.json()["data"])
                assert all(row["id"] != reseller_license["id"] for row in outsider_list.json()["data"])

                # Issuers cannot revoke licenses issued by a different tenant.
                vendor_cross_revoke = await client.post(
                    f"/api/v1/edition/licenses/vendor/{reseller_license['id']}/revoke",
                    headers=headers["vendor"],
                    json={"reason": "must not cross issuer boundary"},
                )
                assert vendor_cross_revoke.status_code == 409, vendor_cross_revoke.text

                reseller_cross_revoke = await client.post(
                    f"/api/v1/edition/licenses/reseller/{vendor_license['id']}/revoke",
                    headers=headers["reseller"],
                    json={"reason": "must not cross issuer boundary"},
                )
                assert reseller_cross_revoke.status_code == 409, reseller_cross_revoke.text

                revoked = await client.post(
                    f"/api/v1/edition/licenses/reseller/{reseller_license['id']}/revoke",
                    headers=headers["reseller"],
                    json={"reason": "customer contract ended"},
                )
                assert revoked.status_code == 200, revoked.text
                revoked_data = revoked.json()["data"]
                assert revoked_data["status"] == "revoked"
                assert revoked_data["revocation_reason"] == "customer contract ended"
                assert "license_key" not in revoked_data
        finally:
            if previous is missing:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
    finally:
        await engine.dispose()
