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
    from app.models.file import FileObject
    from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
    from app.rag import service as rag_service
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
    sibling = Tenant(name=f"Portal sibling reseller {run_id}", slug=f"portal-sibling-{run_id}", status="active", tenant_kind="reseller", access_grant_required=True, settings={})
    sibling.parent = vendor
    vendor_b = Tenant(name=f"Portal test vendor B {run_id}", slug=f"portal-vendor-b-{run_id}", status="active", tenant_kind="vendor", settings={})
    reseller_b = Tenant(name=f"Portal test reseller B {run_id}", slug=f"portal-reseller-b-{run_id}", status="active", tenant_kind="reseller", access_grant_required=True, settings={})
    reseller_b.parent = vendor_b
    customer_a = Tenant(name=f"Portal test customer A {run_id}", slug=f"portal-customer-a-{run_id}", status="active", tenant_kind="customer", access_grant_required=True, settings={})
    customer_a.parent = target
    try:
        async with sessions() as session:
            session.add_all([vendor, target, sibling, vendor_b, reseller_b, customer_a])
            await session.flush()
            grantor = User(
                tenant_id=vendor.id, email=f"portal-grantor-{run_id}@example.com",
                password_hash="not-used", full_name="Portal Grantor", is_active=True,
                is_superuser=False, is_platform_admin=False, roles=[],
            )
            actor = User(
                tenant_id=vendor.id, email=f"portal-actor-{run_id}@example.com",
                password_hash="not-used", full_name="Portal Actor", is_active=True,
                is_superuser=False, is_platform_admin=False, roles=[],
            )
            reseller_grantor = User(tenant_id=target.id, email=f"reseller-grantor-{run_id}@example.com", password_hash="x", full_name="Reseller Grantor", is_active=True, is_superuser=False, is_platform_admin=False, roles=[])
            reseller_actor = User(tenant_id=target.id, email=f"reseller-actor-{run_id}@example.com", password_hash="x", full_name="Reseller Actor", is_active=True, is_superuser=False, is_platform_admin=False, roles=[])
            customer_actor = User(tenant_id=customer_a.id, email=f"customer-actor-{run_id}@example.com", password_hash="x", full_name="Customer Actor", is_active=True, is_superuser=False, is_platform_admin=False, roles=[])
            session.add_all([grantor, actor, reseller_grantor, reseller_actor, customer_actor])
            await session.flush()
            permission = (await session.execute(
                select(Permission).where(Permission.code == "employee.read")
            )).scalar_one_or_none()
            if permission is None:
                permission = Permission(code="employee.read", description="Read employees")
                session.add(permission)
                await session.flush()
            file_permissions = []
            for code in ("file.read", "file.write"):
                file_permission = (await session.execute(select(Permission).where(Permission.code == code))).scalar_one_or_none()
                if file_permission is None:
                    file_permission = Permission(code=code, description=f"Portal test {code}")
                    session.add(file_permission)
                    await session.flush()
                file_permissions.append(file_permission)
            admin_role = Role(tenant_id=vendor.id, name="Admin", description="Portal integration admin")
            reseller_admin_role = Role(tenant_id=target.id, name="Admin", description="Reseller portal admin")
            reader_role = Role(tenant_id=vendor.id, name="Employee Reader", description="Portal integration reader")
            reader_role.permissions = [permission, *file_permissions]
            grantor.roles = [admin_role]
            actor.roles = [reader_role]
            reseller_admin_role.permissions = file_permissions
            reseller_grantor.roles = [reseller_admin_role]
            reseller_actor.roles = [reseller_admin_role]
            customer_file = FileObject(
                tenant_id=customer_a.id,
                uploaded_by=customer_actor.id,
                filename="customer-policy.txt",
                content_type="text/plain",
                size_bytes=14,
                storage_key=f"{customer_a.id}/customer-policy.txt",
                status="active",
            )
            target_file = FileObject(tenant_id=target.id, uploaded_by=actor.id, filename="target-policy.txt", content_type="text/plain", size_bytes=10, storage_key=f"{target.id}/target-policy.txt", status="active")
            sibling_file = FileObject(tenant_id=sibling.id, uploaded_by=actor.id, filename="sibling-secret.txt", content_type="text/plain", size_bytes=12, storage_key=f"{sibling.id}/sibling-secret.txt", status="active")
            cross_vendor_file = FileObject(tenant_id=reseller_b.id, uploaded_by=actor.id, filename="vendor-b-secret.txt", content_type="text/plain", size_bytes=15, storage_key=f"{reseller_b.id}/vendor-b-secret.txt", status="active")
            session.add_all([customer_file, target_file, sibling_file, cross_vendor_file])
            await session.flush()
            sibling_document = KnowledgeDocument(tenant_id=sibling.id, file_id=sibling_file.id, status="indexed", chunk_count=1, embedding_model="portal-test")
            session.add(sibling_document)
            await session.flush()
            session.add_all([
                KnowledgeChunk(tenant_id=sibling.id, document_id=sibling_document.id, chunk_index=0, content="sibling tenant secret", embedding=[1.0] + [0.0] * 63),
            ])
            session.add_all([
                admin_role,
                reseller_admin_role,
                reader_role,
                TenantDemoGrant(
                    tenant_id=target.id,
                    granted_by_user_id=grantor.id,
                    reason="Isolated portal context integration test",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                ),
            ])
            session.add(TenantDemoGrant(tenant_id=customer_a.id, granted_by_user_id=grantor.id, reason="Direct customer portal test", expires_at=datetime.now(timezone.utc) + timedelta(days=1)))
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
        async def deterministic_test_embedding(_texts):
            return [[1.0] + [0.0] * 63 for _ in _texts]

        monkeypatch.setattr(rag_service, "embed_texts", deterministic_test_embedding)
        monkeypatch.setattr(rag_service, "extract_text", lambda _file: "target tenant knowledge")
        try:
            grantor_token = create_access_token(
                subject=grantor.id, tenant_id=vendor.id,
                extra_claims={"auth_token_version": grantor.auth_token_version},
            )
            actor_token = create_access_token(
                subject=actor.id, tenant_id=vendor.id,
                extra_claims={"auth_token_version": actor.auth_token_version},
            )
            reseller_grantor_token = create_access_token(subject=reseller_grantor.id, tenant_id=target.id, extra_claims={"auth_token_version": reseller_grantor.auth_token_version})
            reseller_actor_token = create_access_token(subject=reseller_actor.id, tenant_id=target.id, extra_claims={"auth_token_version": reseller_actor.auth_token_version})
            customer_actor_token = create_access_token(subject=customer_actor.id, tenant_id=customer_a.id, extra_claims={"auth_token_version": customer_actor.auth_token_version})
            grantor_headers = {"Authorization": f"Bearer {grantor_token}"}
            actor_headers = {"Authorization": f"Bearer {actor_token}"}
            reseller_grantor_headers = {"Authorization": f"Bearer {reseller_grantor_token}"}
            reseller_actor_headers = {"Authorization": f"Bearer {reseller_actor_token}"}
            customer_actor_headers = {"Authorization": f"Bearer {customer_actor_token}"}
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

                # A Vendor cannot grant access across another Vendor root or skip
                # its direct Reseller owner to reach a grandchild Customer.
                cross_vendor_grant = await client.post(
                    "/api/v1/edition/vendor/portal-access-grants",
                    headers=grantor_headers,
                    json={"actor_user_id": str(actor.id), "target_tenant_id": str(reseller_b.id), "reason": "Must be denied across Vendor roots"},
                )
                assert cross_vendor_grant.status_code == 403, cross_vendor_grant.text
                grandchild_grant = await client.post(
                    "/api/v1/edition/vendor/portal-access-grants",
                    headers=grantor_headers,
                    json={"actor_user_id": str(actor.id), "target_tenant_id": str(customer_a.id), "reason": "Must not skip the direct Reseller"},
                )
                assert grandchild_grant.status_code == 403, grandchild_grant.text

                reseller_created = await client.post(
                    "/api/v1/edition/reseller/portal-access-grants",
                    headers=reseller_grantor_headers,
                    json={"actor_user_id": str(reseller_actor.id), "target_tenant_id": str(customer_a.id), "reason": "Direct customer portal"},
                )
                assert reseller_created.status_code == 201, reseller_created.text
                reseller_grant_id = reseller_created.json()["data"]["id"]
                reseller_activated = await client.post(
                    f"/api/v1/edition/reseller/portal-access-grants/{reseller_grant_id}/activate",
                    headers=reseller_actor_headers,
                )
                assert reseller_activated.status_code == 200, reseller_activated.text
                customer_portal_token = reseller_activated.json()["data"]["access_token"]
                customer_portal_me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {customer_portal_token}"})
                assert customer_portal_me.status_code == 200, customer_portal_me.text
                assert customer_portal_me.json()["data"]["tenant"]["id"] == str(customer_a.id)
                assert customer_portal_me.json()["data"]["user"]["tenant_id"] == str(target.id)
                # Customer portal resources must resolve against the effective
                # Customer context, not the actor's home Reseller tenant.
                customer_visible_files = await client.get(
                    "/api/v1/files",
                    headers={"Authorization": f"Bearer {customer_portal_token}"},
                )
                assert customer_visible_files.status_code == 200, customer_visible_files.text
                assert [item["id"] for item in customer_visible_files.json()["data"]] == [str(customer_file.id)]
                reseller_file_from_customer = await client.get(
                    f"/api/v1/files/{target_file.id}",
                    headers={"Authorization": f"Bearer {customer_portal_token}"},
                )
                assert reseller_file_from_customer.status_code == 404, reseller_file_from_customer.text
                # A Reseller-to-Customer portal token must not expose the
                # target Customer's user directory or permit user enumeration.
                customer_portal_users = await client.get(
                    "/api/v1/tenant-admin/users",
                    headers={"Authorization": f"Bearer {customer_portal_token}"},
                )
                assert customer_portal_users.status_code == 403, customer_portal_users.text
                # Analytics ROI is an admin-only surface and must remain
                # unavailable to portal-context tokens, even with a valid grant.
                customer_portal_roi = await client.get(
                    "/api/v1/analytics/roi",
                    headers={"Authorization": f"Bearer {customer_portal_token}"},
                )
                assert customer_portal_roi.status_code == 403, customer_portal_roi.text
                customer_escalation = await client.post(
                    "/api/v1/edition/reseller/portal-access-grants",
                    headers=customer_actor_headers,
                    json={"actor_user_id": str(customer_actor.id), "target_tenant_id": str(sibling.id), "reason": "Must be denied"},
                )
                assert customer_escalation.status_code == 403, customer_escalation.text

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

                visible_files = await client.get("/api/v1/files", headers=portal_headers)
                assert visible_files.status_code == 200, visible_files.text
                assert [item["id"] for item in visible_files.json()["data"]] == [str(target_file.id)]
                foreign_file = await client.get(f"/api/v1/files/{sibling_file.id}", headers=portal_headers)
                assert foreign_file.status_code == 404, foreign_file.text
                cross_vendor_file_response = await client.get(f"/api/v1/files/{cross_vendor_file.id}", headers=portal_headers)
                assert cross_vendor_file_response.status_code == 404, cross_vendor_file_response.text
                foreign_index = await client.post("/api/v1/knowledge/index", headers=portal_headers, json={"file_id": str(sibling_file.id)})
                assert foreign_index.status_code == 404, foreign_index.text
                target_index = await client.post("/api/v1/knowledge/index", headers=portal_headers, json={"file_id": str(target_file.id)})
                assert target_index.status_code == 201, target_index.text
                knowledge = await client.post("/api/v1/knowledge/search", headers=portal_headers, json={"query": "tenant policy", "top_k": 20})
                assert knowledge.status_code == 200, knowledge.text
                knowledge_content = [item["content"] for item in knowledge.json()["data"]]
                assert "target tenant knowledge" in knowledge_content
                assert "sibling tenant secret" not in knowledge_content
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
