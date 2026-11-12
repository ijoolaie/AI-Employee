"""PostgreSQL-backed portal grant, context, and immediate revocation contract."""

import os
import uuid
from io import BytesIO
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

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
    from app.core.config import get_settings
    from app.core.database import get_db
    from app.core.security import create_access_token
    from app.main import app
    from app.api.v1 import usage as usage_api

    # This integration test makes many authenticated requests; shared CI Redis
    # buckets can otherwise rate-limit it based on unrelated parallel tests.
    monkeypatch.setattr(get_settings(), "rate_limit_enabled", False)
    from app.models.portal_access_grant import PortalAccessGrant
    from app.models.outbox import OutboxMessage
    from app.models.business_invoice import BusinessInvoice
    from app.models.test_definition import TestDefinition
    from app.models.test_run import TestRun, TestRunStatus
    from app.models.test_run_artifact import TestRunArtifact
    from app.models.ai_provider_call import AIProviderCall
    from app.models.workflow import WorkflowRun
    from app.models.file import FileObject
    from app.models.customer import Customer
    from app.models.employee import Employee
    from app.models.meeting import Meeting, MeetingParticipant
    from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
    from app.rag import service as rag_service
    from app.models.role import Permission, Role
    from app.models.tenant import Tenant
    from app.models.tenant_demo_grant import TenantDemoGrant
    from app.models.user import User
    from app.services import audit_service, customer_dashboard_service, storage as storage_service

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
    unentitled_customer = Tenant(name=f"Portal unentitled customer {run_id}", slug=f"portal-unentitled-customer-{run_id}", status="active", tenant_kind="customer", access_grant_required=True, settings={})
    unentitled_customer.parent = target
    direct_customer = Tenant(name=f"Portal direct Vendor customer {run_id}", slug=f"portal-direct-customer-{run_id}", status="active", tenant_kind="customer", access_grant_required=True, settings={})
    direct_customer.parent = vendor
    try:
        async with sessions() as session:
            session.add_all([vendor, target, sibling, vendor_b, reseller_b, customer_a, unentitled_customer, direct_customer])
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
            vendor_b_grantor = User(
                tenant_id=vendor_b.id, email=f"portal-vendor-b-grantor-{run_id}@example.com",
                password_hash="not-used", full_name="Vendor B Grantor", is_active=True,
                is_superuser=False, is_platform_admin=False, roles=[],
            )
            vendor_b_actor = User(
                tenant_id=vendor_b.id, email=f"portal-vendor-b-actor-{run_id}@example.com",
                password_hash="not-used", full_name="Vendor B Actor", is_active=True,
                is_superuser=False, is_platform_admin=False, roles=[],
            )
            reseller_grantor = User(tenant_id=target.id, email=f"reseller-grantor-{run_id}@example.com", password_hash="x", full_name="Reseller Grantor", is_active=True, is_superuser=False, is_platform_admin=False, roles=[])
            reseller_actor = User(tenant_id=target.id, email=f"reseller-actor-{run_id}@example.com", password_hash="x", full_name="Reseller Actor", is_active=True, is_superuser=False, is_platform_admin=False, roles=[])
            customer_actor = User(tenant_id=customer_a.id, email=f"customer-actor-{run_id}@example.com", password_hash="x", full_name="Customer Actor", is_active=True, is_superuser=False, is_platform_admin=False, roles=[])
            direct_customer_actor = User(tenant_id=direct_customer.id, email=f"direct-customer-actor-{run_id}@example.com", password_hash="x", full_name="Direct Customer Actor", is_active=True, is_superuser=False, is_platform_admin=False, roles=[])
            session.add_all([grantor, actor, vendor_b_grantor, vendor_b_actor, reseller_grantor, reseller_actor, customer_actor, direct_customer_actor])
            await session.flush()
            session.add(TenantDemoGrant(
                tenant_id=direct_customer.id,
                granted_by_user_id=grantor.id,
                reason="Isolated direct Vendor-to-Customer portal acceptance fixture",
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            ))
            permission = (await session.execute(
                select(Permission).where(Permission.code == "employee.read")
            )).scalar_one_or_none()
            if permission is None:
                permission = Permission(code="employee.read", description="Read employees")
                session.add(permission)
                await session.flush()
            file_permissions = []
            for code in ("file.read", "file.write", "privacy.customer.export"):
                file_permission = (await session.execute(select(Permission).where(Permission.code == code))).scalar_one_or_none()
                if file_permission is None:
                    file_permission = Permission(code=code, description=f"Portal test {code}")
                    session.add(file_permission)
                    await session.flush()
                file_permissions.append(file_permission)
            workflow_execute_permission = (
                await session.execute(select(Permission).where(Permission.code == "workflow.execute"))
            ).scalar_one_or_none()
            if workflow_execute_permission is None:
                workflow_execute_permission = Permission(code="workflow.execute", description="Execute workflows")
                session.add(workflow_execute_permission)
                await session.flush()
            workflow_read_permission = (
                await session.execute(select(Permission).where(Permission.code == "workflow.read"))
            ).scalar_one_or_none()
            if workflow_read_permission is None:
                workflow_read_permission = Permission(code="workflow.read", description="Read workflow operations")
                session.add(workflow_read_permission)
                await session.flush()
            invoice_read_permission = (
                await session.execute(select(Permission).where(Permission.code == "invoices.read"))
            ).scalar_one_or_none()
            if invoice_read_permission is None:
                invoice_read_permission = Permission(code="invoices.read", description="Read invoices")
                session.add(invoice_read_permission)
                await session.flush()
            invoice_export_pdf_permission = (
                await session.execute(select(Permission).where(Permission.code == "invoices.export_pdf"))
            ).scalar_one_or_none()
            if invoice_export_pdf_permission is None:
                invoice_export_pdf_permission = Permission(
                    code="invoices.export_pdf", description="Export invoice PDF"
                )
                session.add(invoice_export_pdf_permission)
                await session.flush()
            run_read_permission = (
                await session.execute(select(Permission).where(Permission.code == "run.read"))
            ).scalar_one_or_none()
            if run_read_permission is None:
                run_read_permission = Permission(code="run.read", description="Read Test Center runs")
                session.add(run_read_permission)
                await session.flush()
            workflow_write_permission = (
                await session.execute(select(Permission).where(Permission.code == "workflow.write"))
            ).scalar_one_or_none()
            if workflow_write_permission is None:
                workflow_write_permission = Permission(code="workflow.write", description="Manage workflows")
                session.add(workflow_write_permission)
                await session.flush()
            audit_read_permission = (await session.execute(
                select(Permission).where(Permission.code == "audit.read")
            )).scalar_one_or_none()
            if audit_read_permission is None:
                audit_read_permission = Permission(code="audit.read", description="Read audit data")
                session.add(audit_read_permission)
                await session.flush()
            privacy_export_permission = (await session.execute(
                select(Permission).where(Permission.code == "privacy.customer.export")
            )).scalar_one_or_none()
            if privacy_export_permission is None:
                privacy_export_permission = Permission(
                    code="privacy.customer.export", description="Export customer privacy data"
                )
                session.add(privacy_export_permission)
                await session.flush()
            admin_role = Role(tenant_id=vendor.id, name="Admin", description="Portal integration admin")
            vendor_b_admin_role = Role(tenant_id=vendor_b.id, name="Admin", description="Vendor B portal integration admin")
            vendor_b_reader_role = Role(tenant_id=vendor_b.id, name="Employee Reader", description="Vendor B portal integration reader")
            reseller_admin_role = Role(tenant_id=target.id, name="Admin", description="Reseller portal admin")
            reader_role = Role(tenant_id=vendor.id, name="Employee Reader", description="Portal integration reader")
            reader_role.permissions = [
                permission, *file_permissions, workflow_execute_permission,
                workflow_read_permission, invoice_read_permission, invoice_export_pdf_permission,
                run_read_permission, audit_read_permission,
            ]
            grantor.roles = [admin_role]
            actor.roles = [reader_role]
            vendor_b_grantor.roles = [vendor_b_admin_role]
            vendor_b_reader_role.permissions = [
                *file_permissions, workflow_execute_permission, workflow_read_permission,
                invoice_read_permission, invoice_export_pdf_permission, run_read_permission, audit_read_permission,
            ]
            vendor_b_actor.roles = [vendor_b_reader_role]
            reseller_admin_role.permissions = [
                *file_permissions, workflow_write_permission, invoice_export_pdf_permission, audit_read_permission,
            ]
            reseller_grantor.roles = [reseller_admin_role]
            reseller_actor.roles = [reseller_admin_role]

            # Reproduce the worker identity mismatch using real PostgreSQL rows:
            # the portal actor exists only in the Vendor home tenant, while the
            # delegated Run is scoped to the Reseller tenant.
            from app.services import run_service

            delegated_actor_lookup = await session.execute(
                select(User).where(User.id == actor.id, User.tenant_id == target.id)
            )
            assert delegated_actor_lookup.scalar_one_or_none() is None
            home_actor_lookup = await session.execute(
                select(User).where(User.id == actor.id, User.tenant_id == vendor.id)
            )
            persisted_actor = home_actor_lookup.scalar_one()
            assert run_read_permission.code in run_service._effective_run_tool_permissions(
                persisted_actor, vendor.id
            )
            assert run_read_permission.code not in run_service._effective_run_tool_permissions(
                persisted_actor, target.id
            )

            # The same identity/role mismatch exists one level deeper:
            # a Reseller actor operating in its granted Customer tenant.
            delegated_customer_lookup = await session.execute(
                select(User).where(User.id == reseller_actor.id, User.tenant_id == customer_a.id)
            )
            assert delegated_customer_lookup.scalar_one_or_none() is None
            reseller_home_lookup = await session.execute(
                select(User).where(User.id == reseller_actor.id, User.tenant_id == target.id)
            )
            persisted_reseller_actor = reseller_home_lookup.scalar_one()
            assert audit_read_permission.code in run_service._effective_run_tool_permissions(
                persisted_reseller_actor, target.id
            )
            assert audit_read_permission.code not in run_service._effective_run_tool_permissions(
                persisted_reseller_actor, customer_a.id
            )
            direct_customer_file = FileObject(
                tenant_id=direct_customer.id,
                uploaded_by=direct_customer_actor.id,
                filename="direct-vendor-customer-policy.txt",
                content_type="text/plain",
                size_bytes=24,
                storage_key=f"{direct_customer.id}/direct-vendor-customer-policy.txt",
                status="active",
            )
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
            vendor_b_file = FileObject(
                tenant_id=reseller_b.id, uploaded_by=vendor_b_actor.id,
                filename="vendor-b-target-policy.txt", content_type="text/plain",
                size_bytes=17, storage_key=f"{reseller_b.id}/vendor-b-target-policy.txt",
                status="active",
            )
            session.add_all([direct_customer_file, customer_file, target_file, sibling_file, cross_vendor_file, vendor_b_file])
            target_customer = Customer(tenant_id=target.id, external_key=f"target-customer-{run_id}", name="Target tenant customer", email="target-customer@example.com", notes="target-private-note")
            sibling_customer = Customer(tenant_id=sibling.id, external_key=f"sibling-customer-{run_id}", name="Sibling secret customer", email="sibling-secret@example.com", notes="sibling-private-note")
            customer_portal_customer = Customer(tenant_id=customer_a.id, external_key=f"customer-portal-customer-{run_id}", name="Customer portal record", email="portal-customer@example.com", notes="customer-portal-private-note")
            reseller_private_customer = Customer(tenant_id=target.id, external_key=f"reseller-private-customer-{run_id}", name="Reseller-only customer", email="reseller-private@example.com", notes="reseller-private-note")
            cross_vendor_customer = Customer(tenant_id=reseller_b.id, external_key=f"vendor-b-customer-{run_id}", name="Vendor B private customer", email="vendor-b-private@example.com", notes="vendor-b-private-note")
            session.add_all([target_customer, sibling_customer, customer_portal_customer, reseller_private_customer, cross_vendor_customer])
            session.add_all([
                AIProviderCall(tenant_id=target.id, provider="portal-test", model="target-model", prompt_tokens=7, completion_tokens=5, cost_usd=0.01, latency_ms=25, status="success"),
                AIProviderCall(tenant_id=sibling.id, provider="portal-test", model="sibling-secret-model", prompt_tokens=900, completion_tokens=900, cost_usd=99.0, latency_ms=999, status="success"),
                AIProviderCall(tenant_id=reseller_b.id, provider="portal-test", model="vendor-b-model", prompt_tokens=17, completion_tokens=13, cost_usd=0.03, latency_ms=35, status="success"),
            ])
            target_dead_letter = OutboxMessage(
                tenant_id=target.id, kind="workflow.execute",
                payload={"private_marker": "target-reseller-dead-letter"},
                status="dead", attempts=4, last_error="target-only failure",
                dead_at=datetime.now(timezone.utc),
            )
            sibling_dead_letter = OutboxMessage(
                tenant_id=sibling.id, kind="workflow.execute",
                payload={"private_marker": "sibling-reseller-secret"},
                status="dead", attempts=8, last_error="sibling secret failure",
                dead_at=datetime.now(timezone.utc),
            )
            vendor_b_dead_letter = OutboxMessage(
                tenant_id=reseller_b.id, kind="workflow.execute",
                payload={"private_marker": "vendor-b-secret"},
                status="dead", attempts=9, last_error="Vendor B secret failure",
                dead_at=datetime.now(timezone.utc),
            )
            session.add_all([target_dead_letter, sibling_dead_letter, vendor_b_dead_letter])
            today = datetime.now(timezone.utc).date()
            target_invoice = BusinessInvoice(
                tenant_id=target.id, number=f"TARGET-{run_id}", status="paid",
                currency="USD", customer_name="Target Reseller Customer",
                issue_date=today, subtotal=120, tax_rate=0, tax_amount=0,
                total=120, line_items=[{"description": "target-only", "quantity": 1, "unit_price": 120}],
            )
            sibling_invoice = BusinessInvoice(
                tenant_id=sibling.id, number=f"SIBLING-{run_id}", status="paid",
                currency="USD", customer_name="Sibling Reseller Secret",
                issue_date=today, subtotal=900, tax_rate=0, tax_amount=0,
                total=900, line_items=[{"description": "sibling-secret", "quantity": 1, "unit_price": 900}],
            )
            vendor_b_invoice = BusinessInvoice(
                tenant_id=reseller_b.id, number=f"VENDOR-B-{run_id}", status="paid",
                currency="USD", customer_name="Vendor B Secret Customer",
                issue_date=today, subtotal=9900, tax_rate=0, tax_amount=0,
                total=9900, line_items=[{"description": "vendor-b-secret", "quantity": 1, "unit_price": 9900}],
            )
            customer_invoice = BusinessInvoice(
                tenant_id=customer_a.id, number=f"CUSTOMER-{run_id}", status="paid",
                currency="USD", customer_name="Customer Portal Invoice",
                issue_date=today, subtotal=45, tax_rate=0, tax_amount=0,
                total=45, line_items=[{"description": "customer-only", "quantity": 1, "unit_price": 45}],
            )
            session.add_all([
                target_dead_letter, sibling_dead_letter, vendor_b_dead_letter,
                target_invoice, sibling_invoice, vendor_b_invoice, customer_invoice,
            ])
            test_center_rows = []
            for tenant, marker in ((target, "target"), (sibling, "sibling"), (reseller_b, "vendor-b")):
                definition = TestDefinition(
                    tenant_id=tenant.id, code=f"portal-{marker}-{run_id}",
                    name=f"{marker} private verification", workspace_key="ops",
                    edition="shared", enabled=True, prerequisites={}, expected_result={},
                    evidence_requirements={},
                )
                session.add(definition)
                await session.flush()
                test_run = TestRun(
                    tenant_id=tenant.id, test_definition_id=definition.id,
                    workspace_key="ops", status=TestRunStatus.PASSED,
                    executor_type="backend", fixtures={"tenant_marker": marker},
                    result={"private_result": f"{marker}-result"},
                    evidence={"private_evidence": f"{marker}-evidence"},
                )
                session.add(test_run)
                await session.flush()
                artifact = TestRunArtifact(
                    tenant_id=tenant.id, test_run_id=test_run.id,
                    artifact_type="log", label=f"{marker}-private-artifact",
                    reference=f"evidence://{marker}/{run_id}",
                    metadata={"tenant_marker": marker},
                )
                session.add(artifact)
                test_center_rows.append((tenant, test_run, definition, artifact))
            target_test_run = test_center_rows[0][1]
            sibling_test_run = test_center_rows[1][1]
            vendor_b_test_run = test_center_rows[2][1]
            await session.flush()
            target_dashboard_employee = Employee(
                tenant_id=target.id, slug=f"target-dashboard-{run_id}",
                name="Target dashboard employee", kind="custom", is_active=True,
            )
            sibling_dashboard_employee = Employee(
                tenant_id=sibling.id, slug=f"sibling-dashboard-{run_id}",
                name="Sibling dashboard secret", kind="custom", is_active=True,
            )
            session.add_all([target_dashboard_employee, sibling_dashboard_employee])
            await session.flush()
            target_meeting = Meeting(
                tenant_id=target.id, title=f"Target reseller meeting {run_id}",
                description="Target tenant meeting",
            )
            sibling_meeting = Meeting(
                tenant_id=sibling.id, title=f"Sibling private meeting {run_id}",
                description="Sibling tenant secret",
            )
            session.add_all([target_meeting, sibling_meeting])
            await session.flush()
            session.add_all([
                MeetingParticipant(
                    tenant_id=target.id, meeting_id=target_meeting.id,
                    employee_id=target_dashboard_employee.id, role="host",
                ),
                # Deliberately inconsistent association: the meeting row is
                # target-owned, but the participant Employee belongs to a
                # sibling tenant. The service must exclude it by Employee.tenant_id.
                MeetingParticipant(
                    tenant_id=target.id, meeting_id=target_meeting.id,
                    employee_id=sibling_dashboard_employee.id, role="observer",
                ),
            ])
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
                vendor_b_admin_role,
                vendor_b_reader_role,
                TenantDemoGrant(
                    tenant_id=target.id,
                    granted_by_user_id=grantor.id,
                    reason="Isolated portal context integration test",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                ),
            ])
            session.add(TenantDemoGrant(tenant_id=customer_a.id, granted_by_user_id=grantor.id, reason="Direct customer portal test", expires_at=datetime.now(timezone.utc) + timedelta(days=1)))
            session.add(TenantDemoGrant(
                tenant_id=reseller_b.id, granted_by_user_id=vendor_b_grantor.id,
                reason="Independent Vendor B portal test",
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            ))
            # Simulate a legacy/corrupt grant row: activation must still reject
            # a Reseller actor attempting to enter its parent Vendor portal.
            reseller_vendor_grant_id = uuid.uuid4()
            session.add(PortalAccessGrant(
                id=reseller_vendor_grant_id,
                actor_user_id=reseller_actor.id,
                actor_tenant_id=target.id,
                target_tenant_id=vendor.id,
                granted_by_user_id=grantor.id,
                reason="Invalid legacy Reseller-to-Vendor grant for denial coverage",
            ))
            # Simulate a stale/corrupt grant to a child with no paid or Demo
            # entitlement. Listing and activation must both fail closed even
            # though the direct-child relationship and grant row look valid.
            unentitled_sibling_grant_id = uuid.uuid4()
            session.add(PortalAccessGrant(
                id=unentitled_sibling_grant_id,
                actor_user_id=actor.id,
                actor_tenant_id=vendor.id,
                target_tenant_id=sibling.id,
                granted_by_user_id=grantor.id,
                reason="Unentitled sibling grant for portal activation denial coverage",
            ))
            unentitled_customer_grant_id = uuid.uuid4()
            session.add(PortalAccessGrant(
                id=unentitled_customer_grant_id,
                actor_user_id=reseller_actor.id,
                actor_tenant_id=target.id,
                target_tenant_id=unentitled_customer.id,
                granted_by_user_id=reseller_grantor.id,
                reason="Unentitled Reseller child grant for portal activation denial coverage",
            ))
            # Audit ledgers are tenant-scoped independently of the portal actor's
            # home tenant. Seed distinct records to prove both Vendor roots resolve
            # only the audit entries owned by the active Reseller context.
            await audit_service.record(
                session, tenant_id=target.id, actor_id=actor.id,
                action="portal.acceptance.vendor-a.target", resource_type="acceptance",
            )
            await audit_service.record(
                session, tenant_id=sibling.id, actor_id=actor.id,
                action="portal.acceptance.vendor-a.sibling", resource_type="acceptance",
            )
            await audit_service.record(
                session, tenant_id=reseller_b.id, actor_id=vendor_b_actor.id,
                action="portal.acceptance.vendor-b.target", resource_type="acceptance",
            )
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
        # Seeded FileObject rows intentionally avoid provider-specific storage.
        # This deterministic backend lets the live API test exercise the actual
        # authenticated streaming-download route and its tenant/context guards.
        class _PortalTestStorageBackend:
            def __init__(self):
                self.objects = {}

            def save(self, key, data):
                content = data.read()
                self.objects[key] = content
                return len(content)

            def open(self, key):
                if key in self.objects:
                    return BytesIO(self.objects[key])
                return BytesIO(f"portal-file-content:{key}".encode())

            def delete(self, key):
                self.objects.pop(key, None)

        test_storage_backend = _PortalTestStorageBackend()
        monkeypatch.setattr(
            storage_service, "get_storage_backend", lambda: test_storage_backend
        )
        try:
            grantor_token = create_access_token(
                subject=grantor.id, tenant_id=vendor.id,
                extra_claims={"auth_token_version": grantor.auth_token_version},
            )
            actor_token = create_access_token(
                subject=actor.id, tenant_id=vendor.id,
                extra_claims={"auth_token_version": actor.auth_token_version},
            )
            vendor_b_grantor_token = create_access_token(
                subject=vendor_b_grantor.id, tenant_id=vendor_b.id,
                extra_claims={"auth_token_version": vendor_b_grantor.auth_token_version},
            )
            vendor_b_actor_token = create_access_token(
                subject=vendor_b_actor.id, tenant_id=vendor_b.id,
                extra_claims={"auth_token_version": vendor_b_actor.auth_token_version},
            )
            reseller_grantor_token = create_access_token(subject=reseller_grantor.id, tenant_id=target.id, extra_claims={"auth_token_version": reseller_grantor.auth_token_version})
            reseller_actor_token = create_access_token(subject=reseller_actor.id, tenant_id=target.id, extra_claims={"auth_token_version": reseller_actor.auth_token_version})
            customer_actor_token = create_access_token(subject=customer_actor.id, tenant_id=customer_a.id, extra_claims={"auth_token_version": customer_actor.auth_token_version})
            grantor_headers = {"Authorization": f"Bearer {grantor_token}"}
            actor_headers = {"Authorization": f"Bearer {actor_token}"}
            vendor_b_grantor_headers = {"Authorization": f"Bearer {vendor_b_grantor_token}"}
            vendor_b_actor_headers = {"Authorization": f"Bearer {vendor_b_actor_token}"}
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

                own_grants = await client.get(
                    "/api/v1/edition/portal-access/my-grants",
                    headers=actor_headers,
                )
                assert own_grants.status_code == 200, own_grants.text
                own_grant_rows = own_grants.json()["data"]
                assert [row["id"] for row in own_grant_rows] == [grant_id]
                assert own_grant_rows[0]["target_tenant_id"] == str(target.id)
                assert own_grant_rows[0]["target_kind"] == "reseller"
                assert own_grant_rows[0]["target_name"] == target.name
                assert all(row["target_tenant_id"] != str(sibling.id) for row in own_grant_rows)
                unentitled_activation = await client.post(
                    f"/api/v1/edition/vendor/portal-access-grants/{unentitled_sibling_grant_id}/activate",
                    headers=actor_headers,
                )
                assert unentitled_activation.status_code == 402, unentitled_activation.text

                # A Vendor may also grant its actor access to a direct Customer,
                # not only a direct Reseller. The token keeps the Vendor as the
                # primary identity while scoping resource reads to that Customer.
                direct_customer_created = await client.post(
                    "/api/v1/edition/vendor/portal-access-grants",
                    headers=grantor_headers,
                    json={
                        "actor_user_id": str(actor.id),
                        "target_tenant_id": str(direct_customer.id),
                        "reason": "Direct Vendor-owned Customer portal acceptance",
                    },
                )
                assert direct_customer_created.status_code == 201, direct_customer_created.text
                direct_customer_grant_id = direct_customer_created.json()["data"]["id"]
                direct_customer_activated = await client.post(
                    f"/api/v1/edition/vendor/portal-access-grants/{direct_customer_grant_id}/activate",
                    headers=actor_headers,
                )
                assert direct_customer_activated.status_code == 200, direct_customer_activated.text
                direct_customer_portal_headers = {
                    "Authorization": f"Bearer {direct_customer_activated.json()['data']['access_token']}",
                }
                direct_customer_me = await client.get(
                    "/api/v1/auth/me", headers=direct_customer_portal_headers,
                )
                assert direct_customer_me.status_code == 200, direct_customer_me.text
                assert direct_customer_me.json()["data"]["tenant"]["id"] == str(direct_customer.id)
                assert direct_customer_me.json()["data"]["user"]["tenant_id"] == str(vendor.id)
                direct_customer_files = await client.get(
                    "/api/v1/files", headers=direct_customer_portal_headers,
                )
                assert direct_customer_files.status_code == 200, direct_customer_files.text
                assert [item["id"] for item in direct_customer_files.json()["data"]] == [
                    str(direct_customer_file.id)
                ]
                direct_customer_download = await client.get(
                    f"/api/v1/files/{direct_customer_file.id}/download",
                    headers=direct_customer_portal_headers,
                )
                assert direct_customer_download.status_code == 200, direct_customer_download.text
                assert direct_customer_download.content == (
                    f"portal-file-content:{direct_customer_file.storage_key}".encode()
                )
                direct_customer_foreign_download = await client.get(
                    f"/api/v1/files/{target_file.id}/download",
                    headers=direct_customer_portal_headers,
                )
                assert direct_customer_foreign_download.status_code == 404, (
                    direct_customer_foreign_download.text
                )
                # The direct Vendor-to-Customer portal must enforce the same
                # complete file lifecycle boundary as Vendor-to-Reseller.
                direct_customer_uploaded_file = await client.post(
                    "/api/v1/files",
                    headers=direct_customer_portal_headers,
                    files={
                        "file": (
                            "direct-customer-upload.txt",
                            b"direct-customer-upload-content",
                            "text/plain",
                        )
                    },
                )
                assert direct_customer_uploaded_file.status_code == 201, (
                    direct_customer_uploaded_file.text
                )
                direct_customer_uploaded_id = (
                    direct_customer_uploaded_file.json()["data"]["id"]
                )
                direct_customer_uploaded_get = await client.get(
                    f"/api/v1/files/{direct_customer_uploaded_id}",
                    headers=direct_customer_portal_headers,
                )
                assert direct_customer_uploaded_get.status_code == 200, (
                    direct_customer_uploaded_get.text
                )
                assert direct_customer_uploaded_get.json()["data"]["filename"] == (
                    "direct-customer-upload.txt"
                )
                direct_customer_uploaded_download = await client.get(
                    f"/api/v1/files/{direct_customer_uploaded_id}/download",
                    headers=direct_customer_portal_headers,
                )
                assert direct_customer_uploaded_download.status_code == 200, (
                    direct_customer_uploaded_download.text
                )
                assert direct_customer_uploaded_download.content == (
                    b"direct-customer-upload-content"
                )
                vendor_home_cannot_read_direct_customer_upload = await client.get(
                    f"/api/v1/files/{direct_customer_uploaded_id}",
                    headers=actor_headers,
                )
                assert vendor_home_cannot_read_direct_customer_upload.status_code == 404, (
                    vendor_home_cannot_read_direct_customer_upload.text
                )
                direct_customer_uploaded_deleted = await client.delete(
                    f"/api/v1/files/{direct_customer_uploaded_id}",
                    headers=direct_customer_portal_headers,
                )
                assert direct_customer_uploaded_deleted.status_code == 200, (
                    direct_customer_uploaded_deleted.text
                )
                direct_customer_deleted_get = await client.get(
                    f"/api/v1/files/{direct_customer_uploaded_id}",
                    headers=direct_customer_portal_headers,
                )
                assert direct_customer_deleted_get.status_code == 404, (
                    direct_customer_deleted_get.text
                )
                direct_customer_deleted_download = await client.get(
                    f"/api/v1/files/{direct_customer_uploaded_id}/download",
                    headers=direct_customer_portal_headers,
                )
                assert direct_customer_deleted_download.status_code == 404, (
                    direct_customer_deleted_download.text
                )

                direct_customer_revoked = await client.delete(
                    f"/api/v1/edition/vendor/portal-access-grants/{direct_customer_grant_id}",
                    headers=grantor_headers,
                )
                assert direct_customer_revoked.status_code == 200, direct_customer_revoked.text
                direct_customer_revoked_me = await client.get(
                    "/api/v1/auth/me", headers=direct_customer_portal_headers,
                )
                assert direct_customer_revoked_me.status_code == 403, direct_customer_revoked_me.text
                direct_customer_revoked_files = await client.get(
                    "/api/v1/files", headers=direct_customer_portal_headers,
                )
                assert direct_customer_revoked_files.status_code == 403, (
                    direct_customer_revoked_files.text
                )
                direct_customer_revoked_download = await client.get(
                    f"/api/v1/files/{direct_customer_file.id}/download",
                    headers=direct_customer_portal_headers,
                )
                assert direct_customer_revoked_download.status_code == 403, (
                    direct_customer_revoked_download.text
                )

                # Vendor B independently grants its own actor access to its own
                # direct Reseller; Vendor A's grant is never inherited.
                vendor_b_created = await client.post(
                    "/api/v1/edition/vendor/portal-access-grants",
                    headers=vendor_b_grantor_headers,
                    json={
                        "actor_user_id": str(vendor_b_actor.id),
                        "target_tenant_id": str(reseller_b.id),
                        "reason": "Independent Vendor B direct Reseller access",
                    },
                )
                assert vendor_b_created.status_code == 201, vendor_b_created.text
                vendor_b_grant_id = vendor_b_created.json()["data"]["id"]
                vendor_b_activated = await client.post(
                    f"/api/v1/edition/vendor/portal-access-grants/{vendor_b_grant_id}/activate",
                    headers=vendor_b_actor_headers,
                )
                assert vendor_b_activated.status_code == 200, vendor_b_activated.text
                vendor_b_portal_headers = {
                    "Authorization": f"Bearer {vendor_b_activated.json()['data']['access_token']}",
                }
                vendor_b_me = await client.get(
                    "/api/v1/auth/me", headers=vendor_b_portal_headers,
                )
                assert vendor_b_me.status_code == 200, vendor_b_me.text
                assert vendor_b_me.json()["data"]["tenant"]["id"] == str(reseller_b.id)
                assert vendor_b_me.json()["data"]["user"]["tenant_id"] == str(vendor_b.id)
                vendor_b_visible_files = await client.get(
                    "/api/v1/files", headers=vendor_b_portal_headers,
                )
                assert vendor_b_visible_files.status_code == 200, vendor_b_visible_files.text
                assert {item["id"] for item in vendor_b_visible_files.json()["data"]} == {
                    str(cross_vendor_file.id),
                    str(vendor_b_file.id),
                }
                vendor_b_cannot_read_vendor_a_file = await client.get(
                    f"/api/v1/files/{target_file.id}", headers=vendor_b_portal_headers,
                )
                assert vendor_b_cannot_read_vendor_a_file.status_code == 404, (
                    vendor_b_cannot_read_vendor_a_file.text
                )
                vendor_b_file_download = await client.get(
                    f"/api/v1/files/{vendor_b_file.id}/download",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_file_download.status_code == 200, vendor_b_file_download.text
                assert vendor_b_file_download.content == (
                    f"portal-file-content:{vendor_b_file.storage_key}".encode()
                )
                vendor_b_foreign_file_download = await client.get(
                    f"/api/v1/files/{target_file.id}/download",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_foreign_file_download.status_code == 404, (
                    vendor_b_foreign_file_download.text
                )

                # Exercise the full tenant-scoped file lifecycle while the
                # actor is in Vendor B's delegated Reseller context.
                vendor_b_uploaded_file = await client.post(
                    "/api/v1/files",
                    headers=vendor_b_portal_headers,
                    files={
                        "file": (
                            "vendor-b-upload.txt",
                            b"vendor-b-upload-content",
                            "text/plain",
                        )
                    },
                )
                assert vendor_b_uploaded_file.status_code == 201, (
                    vendor_b_uploaded_file.text
                )
                uploaded_file_id = vendor_b_uploaded_file.json()["data"]["id"]
                vendor_b_uploaded_file_get = await client.get(
                    f"/api/v1/files/{uploaded_file_id}",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_uploaded_file_get.status_code == 200, (
                    vendor_b_uploaded_file_get.text
                )
                assert vendor_b_uploaded_file_get.json()["data"]["filename"] == (
                    "vendor-b-upload.txt"
                )
                vendor_b_uploaded_file_download = await client.get(
                    f"/api/v1/files/{uploaded_file_id}/download",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_uploaded_file_download.status_code == 200, (
                    vendor_b_uploaded_file_download.text
                )
                assert vendor_b_uploaded_file_download.content == (
                    b"vendor-b-upload-content"
                )
                vendor_a_cannot_read_vendor_b_upload = await client.get(
                    f"/api/v1/files/{uploaded_file_id}",
                    headers=actor_headers,
                )
                assert vendor_a_cannot_read_vendor_b_upload.status_code == 404, (
                    vendor_a_cannot_read_vendor_b_upload.text
                )
                vendor_b_uploaded_file_deleted = await client.delete(
                    f"/api/v1/files/{uploaded_file_id}",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_uploaded_file_deleted.status_code == 200, (
                    vendor_b_uploaded_file_deleted.text
                )
                vendor_b_deleted_file_get = await client.get(
                    f"/api/v1/files/{uploaded_file_id}",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_deleted_file_get.status_code == 404, (
                    vendor_b_deleted_file_get.text
                )
                vendor_b_deleted_file_download = await client.get(
                    f"/api/v1/files/{uploaded_file_id}/download",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_deleted_file_download.status_code == 404, (
                    vendor_b_deleted_file_download.text
                )

                vendor_b_customer_export = await client.get(
                    f"/api/v1/privacy/customers/{cross_vendor_customer.id}/export",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_customer_export.status_code == 200, vendor_b_customer_export.text
                assert vendor_b_customer_export.json()["data"]["customer"]["id"] == str(
                    cross_vendor_customer.id
                )
                vendor_b_cannot_export_vendor_a_customer = await client.get(
                    f"/api/v1/privacy/customers/{target_customer.id}/export",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_cannot_export_vendor_a_customer.status_code == 404, (
                    vendor_b_cannot_export_vendor_a_customer.text
                )

                vendor_b_audit = await client.get(
                    "/api/v1/operations/audit-logs", headers=vendor_b_portal_headers,
                )
                assert vendor_b_audit.status_code == 200, vendor_b_audit.text
                vendor_b_audit_actions = {item["action"] for item in vendor_b_audit.json()["data"]}
                assert "portal.acceptance.vendor-b.target" in vendor_b_audit_actions
                assert "portal.acceptance.vendor-a.target" not in vendor_b_audit_actions
                assert "portal.acceptance.vendor-a.sibling" not in vendor_b_audit_actions
                # A valid Vendor B portal grant must not expose either tenant's
                # private handoff-notification settings through tenant administration.
                vendor_b_notification_read = await client.get(
                    "/api/v1/tenant-admin/customer-handoff-notification",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_notification_read.status_code == 403, vendor_b_notification_read.text
                vendor_b_notification_write = await client.put(
                    "/api/v1/tenant-admin/customer-handoff-notification",
                    headers=vendor_b_portal_headers,
                    json={"email": "vendor-b-portal-override@example.com"},
                )
                assert vendor_b_notification_write.status_code == 403, vendor_b_notification_write.text
                # Vendor B usage and invoice reports must resolve only to its Reseller.
                vendor_b_usage = await client.get("/api/v1/usage/summary", headers=vendor_b_portal_headers)
                assert vendor_b_usage.status_code == 200, vendor_b_usage.text
                vendor_b_usage_data = vendor_b_usage.json()["data"]
                assert vendor_b_usage_data["calls"] == 1
                assert vendor_b_usage_data["prompt_tokens"] == 17
                assert vendor_b_usage_data["completion_tokens"] == 13
                assert vendor_b_usage_data["total_tokens"] == 30
                assert vendor_b_usage_data["cost_usd"] == 0.03

                vendor_b_invoices = await client.get("/api/v1/invoices", headers=vendor_b_portal_headers)
                assert vendor_b_invoices.status_code == 200, vendor_b_invoices.text
                assert [item["id"] for item in vendor_b_invoices.json()["data"]] == [str(vendor_b_invoice.id)]
                vendor_b_foreign_invoice = await client.get(
                    f"/api/v1/invoices/{target_invoice.id}", headers=vendor_b_portal_headers,
                )
                assert vendor_b_foreign_invoice.status_code == 404, vendor_b_foreign_invoice.text
                vendor_b_invoice_summary = await client.get(
                    "/api/v1/invoices/summary", headers=vendor_b_portal_headers,
                )
                assert vendor_b_invoice_summary.status_code == 200, vendor_b_invoice_summary.text
                vendor_b_summary_data = vendor_b_invoice_summary.json()["data"]
                assert vendor_b_summary_data["total_invoices"] == 1
                assert vendor_b_summary_data["counts_by_status"] == {"paid": 1}
                assert vendor_b_summary_data["currency_breakdown"]["USD"]["collected"] == 9900.0
                vendor_b_pdf_export = await client.post(
                    f"/api/v1/invoices/{vendor_b_invoice.id}/export-pdf",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_pdf_export.status_code == 200, vendor_b_pdf_export.text
                vendor_b_pdf_id = vendor_b_pdf_export.json()["data"]["pdf_file_id"]
                async with sessions() as session:
                    vendor_b_pdf_row = await session.get(FileObject, uuid.UUID(vendor_b_pdf_id))
                    assert vendor_b_pdf_row is not None
                    assert vendor_b_pdf_row.tenant_id == reseller_b.id
                    assert vendor_b_pdf_row.uploaded_by == vendor_b_actor.id

                vendor_b_verification = await client.get(
                    f"/api/v1/test-center/runs/{vendor_b_test_run.id}/verification-record",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_verification.status_code == 200, vendor_b_verification.text
                assert vendor_b_verification.json()["tenant_id"] == str(reseller_b.id)
                assert [item["label"] for item in vendor_b_verification.json()["artifacts"]] == [
                    "vendor-b-private-artifact"
                ]
                vendor_b_foreign_verification = await client.get(
                    f"/api/v1/test-center/runs/{target_test_run.id}/verification-record",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_foreign_verification.status_code == 404, vendor_b_foreign_verification.text

                vendor_b_operations = await client.get(
                    "/api/v1/operations/metrics", headers=vendor_b_portal_headers,
                )
                assert vendor_b_operations.status_code == 200, vendor_b_operations.text
                vendor_b_metrics = vendor_b_operations.json()["data"]
                assert vendor_b_metrics["outbox"]["dead"] == 1
                assert vendor_b_metrics["ai"]["calls"] == 1
                assert vendor_b_metrics["ai"]["tokens"] == 30
                assert vendor_b_metrics["ai"]["cost_usd"] == 0.03

                vendor_b_dead_letters = await client.get(
                    "/api/v1/operations/dead-letters", headers=vendor_b_portal_headers,
                )
                assert vendor_b_dead_letters.status_code == 200, vendor_b_dead_letters.text
                assert [item["id"] for item in vendor_b_dead_letters.json()["data"]] == [
                    str(vendor_b_dead_letter.id)
                ]
                assert "target-reseller-dead-letter" not in str(vendor_b_dead_letters.json()["data"])
                vendor_b_foreign_dead_letter = await client.post(
                    f"/api/v1/operations/dead-letters/{target_dead_letter.id}/replay",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_foreign_dead_letter.status_code == 404, vendor_b_foreign_dead_letter.text

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

                # Reseller identities cannot enter or administer the Vendor portal,
                # even when they attempt the Vendor grant API directly.
                reseller_cannot_list_vendor_grants = await client.get(
                    "/api/v1/edition/vendor/portal-access-grants",
                    headers=reseller_actor_headers,
                )
                assert reseller_cannot_list_vendor_grants.status_code == 403, (
                    reseller_cannot_list_vendor_grants.text
                )
                reseller_cannot_create_vendor_grant = await client.post(
                    "/api/v1/edition/vendor/portal-access-grants",
                    headers=reseller_actor_headers,
                    json={
                        "actor_user_id": str(reseller_actor.id),
                        "target_tenant_id": str(target.id),
                        "reason": "Reseller cannot delegate Vendor portal access",
                    },
                )
                assert reseller_cannot_create_vendor_grant.status_code == 403, (
                    reseller_cannot_create_vendor_grant.text
                )
                # Even a pre-existing invalid grant cannot elevate a Reseller
                # into its parent Vendor portal through either activation route.
                reseller_cannot_activate_vendor_portal = await client.post(
                    f"/api/v1/edition/vendor/portal-access-grants/{reseller_vendor_grant_id}/activate",
                    headers=reseller_actor_headers,
                )
                assert reseller_cannot_activate_vendor_portal.status_code == 403, (
                    reseller_cannot_activate_vendor_portal.text
                )
                reseller_cannot_activate_parent_vendor_via_reseller_route = await client.post(
                    f"/api/v1/edition/reseller/portal-access-grants/{reseller_vendor_grant_id}/activate",
                    headers=reseller_actor_headers,
                )
                assert reseller_cannot_activate_parent_vendor_via_reseller_route.status_code == 403, (
                    reseller_cannot_activate_parent_vendor_via_reseller_route.text
                )

                reseller_created = await client.post(
                    "/api/v1/edition/reseller/portal-access-grants",
                    headers=reseller_grantor_headers,
                    json={"actor_user_id": str(reseller_actor.id), "target_tenant_id": str(customer_a.id), "reason": "Direct customer portal"},
                )
                assert reseller_created.status_code == 201, reseller_created.text
                reseller_grant_id = reseller_created.json()["data"]["id"]
                reseller_own_grants = await client.get(
                    "/api/v1/edition/portal-access/my-grants",
                    headers=reseller_actor_headers,
                )
                assert reseller_own_grants.status_code == 200, reseller_own_grants.text
                reseller_own_grant_rows = reseller_own_grants.json()["data"]
                assert [row["id"] for row in reseller_own_grant_rows] == [reseller_grant_id]
                assert all(
                    row["target_tenant_id"] != str(unentitled_customer.id)
                    for row in reseller_own_grant_rows
                )
                unentitled_customer_activation = await client.post(
                    f"/api/v1/edition/reseller/portal-access-grants/{unentitled_customer_grant_id}/activate",
                    headers=reseller_actor_headers,
                )
                assert unentitled_customer_activation.status_code == 402, (
                    unentitled_customer_activation.text
                )
                workflow_created = await client.post(
                    "/api/v1/workflows", headers=reseller_grantor_headers,
                    json={
                        "slug": f"portal-workflow-{run_id}",
                        "name": "Portal context workflow dispatch",
                        "steps": [{"key": "approval", "type": "approval", "message": "Review portal task"}],
                    },
                )
                assert workflow_created.status_code == 201, workflow_created.text
                workflow_id = workflow_created.json()["data"]["id"]
                reseller_activated = await client.post(
                    f"/api/v1/edition/reseller/portal-access-grants/{reseller_grant_id}/activate",
                    headers=reseller_actor_headers,
                )
                assert reseller_activated.status_code == 200, reseller_activated.text
                customer_portal_token = reseller_activated.json()["data"]["access_token"]
                customer_portal_headers = {"Authorization": f"Bearer {customer_portal_token}"}
                customer_portal_me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {customer_portal_token}"})
                assert customer_portal_me.status_code == 200, customer_portal_me.text
                assert customer_portal_me.json()["data"]["tenant"]["id"] == str(customer_a.id)
                assert customer_portal_me.json()["data"]["user"]["tenant_id"] == str(target.id)
                customer_invoice_export = await client.post(
                    f"/api/v1/invoices/{customer_invoice.id}/export-pdf",
                    headers=customer_portal_headers,
                )
                assert customer_invoice_export.status_code == 200, customer_invoice_export.text
                customer_pdf_id = customer_invoice_export.json()["data"]["pdf_file_id"]
                async with sessions() as session:
                    customer_pdf_row = await session.get(FileObject, uuid.UUID(customer_pdf_id))
                    assert customer_pdf_row is not None
                    assert customer_pdf_row.tenant_id == customer_a.id
                    assert customer_pdf_row.uploaded_by == reseller_actor.id
                customer_parent_invoice_export = await client.post(
                    f"/api/v1/invoices/{target_invoice.id}/export-pdf",
                    headers=customer_portal_headers,
                )
                assert customer_parent_invoice_export.status_code == 404, customer_parent_invoice_export.text
                # Customer portal resources must resolve against the effective
                # Customer context, not the actor's home Reseller tenant.
                customer_visible_files = await client.get(
                    "/api/v1/files",
                    headers={"Authorization": f"Bearer {customer_portal_token}"},
                )
                assert customer_visible_files.status_code == 200, customer_visible_files.text
                assert {item["id"] for item in customer_visible_files.json()["data"]} == {
                    str(customer_file.id), customer_pdf_id,
                }
                customer_file_download = await client.get(
                    f"/api/v1/files/{customer_file.id}/download",
                    headers={"Authorization": f"Bearer {customer_portal_token}"},
                )
                assert customer_file_download.status_code == 200, customer_file_download.text
                assert customer_file_download.content == (
                    f"portal-file-content:{customer_file.storage_key}".encode()
                )
                reseller_file_from_customer = await client.get(
                    f"/api/v1/files/{target_file.id}",
                    headers={"Authorization": f"Bearer {customer_portal_token}"},
                )
                assert reseller_file_from_customer.status_code == 404, reseller_file_from_customer.text
                reseller_file_download_from_customer = await client.get(
                    f"/api/v1/files/{target_file.id}/download",
                    headers={"Authorization": f"Bearer {customer_portal_token}"},
                )
                assert reseller_file_download_from_customer.status_code == 404, (
                    reseller_file_download_from_customer.text
                )
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
                customer_portal_export = await client.get(
                    f"/api/v1/privacy/customers/{customer_portal_customer.id}/export",
                    headers={"Authorization": f"Bearer {customer_portal_token}"},
                )
                assert customer_portal_export.status_code == 200, customer_portal_export.text
                assert customer_portal_export.json()["data"]["customer"]["id"] == str(customer_portal_customer.id)
                reseller_private_export = await client.get(
                    f"/api/v1/privacy/customers/{reseller_private_customer.id}/export",
                    headers=customer_portal_headers,
                )
                assert reseller_private_export.status_code == 404, reseller_private_export.text
                customer_pdf_download = await client.get(
                    f"/api/v1/files/{customer_pdf_id}/download", headers=customer_portal_headers,
                )
                assert customer_pdf_download.status_code == 200, customer_pdf_download.text
                assert customer_pdf_download.headers.get("content-type", "").startswith("application/pdf")

                # Customer identities cannot enumerate or create Vendor/Reseller
                # portal grants, even when targeting an otherwise related tenant.
                customer_vendor_grants = await client.get(
                    "/api/v1/edition/vendor/portal-access-grants",
                    headers=customer_actor_headers,
                )
                assert customer_vendor_grants.status_code == 403, customer_vendor_grants.text
                customer_reseller_grants = await client.get(
                    "/api/v1/edition/reseller/portal-access-grants",
                    headers=customer_actor_headers,
                )
                assert customer_reseller_grants.status_code == 403, customer_reseller_grants.text
                # Action grants control delegated Vendor/Reseller provisioning;
                # Customer identities must not enumerate, create, or revoke them.
                customer_vendor_action_grants = await client.get(
                    "/api/v1/edition/vendor/action-grants",
                    headers=customer_actor_headers,
                )
                assert customer_vendor_action_grants.status_code == 403, customer_vendor_action_grants.text
                customer_reseller_action_grants = await client.get(
                    "/api/v1/edition/reseller/action-grants",
                    headers=customer_actor_headers,
                )
                assert customer_reseller_action_grants.status_code == 403, customer_reseller_action_grants.text
                action_grant_payload = {
                    "user_id": str(customer_actor.id),
                    "action_code": "vendor.customer.create",
                    "reason": "Customer identities cannot delegate tenant provisioning",
                    "expires_in_days": 30,
                }
                customer_vendor_action_grant_create = await client.post(
                    "/api/v1/edition/vendor/action-grants",
                    headers=customer_actor_headers,
                    json=action_grant_payload,
                )
                assert customer_vendor_action_grant_create.status_code == 403, (
                    customer_vendor_action_grant_create.text
                )
                customer_reseller_action_grant_create = await client.post(
                    "/api/v1/edition/reseller/action-grants",
                    headers=customer_actor_headers,
                    json={**action_grant_payload, "action_code": "reseller.customer.create"},
                )
                assert customer_reseller_action_grant_create.status_code == 403, (
                    customer_reseller_action_grant_create.text
                )
                customer_vendor_action_grant_revoke = await client.delete(
                    f"/api/v1/edition/vendor/action-grants/{uuid.uuid4()}",
                    headers=customer_actor_headers,
                )
                assert customer_vendor_action_grant_revoke.status_code == 403, (
                    customer_vendor_action_grant_revoke.text
                )
                customer_reseller_action_grant_revoke = await client.delete(
                    f"/api/v1/edition/reseller/action-grants/{uuid.uuid4()}",
                    headers=customer_actor_headers,
                )
                assert customer_reseller_action_grant_revoke.status_code == 403, (
                    customer_reseller_action_grant_revoke.text
                )
                customer_cannot_enumerate_tenant_users = await client.get(
                    "/api/v1/tenant-admin/users",
                    headers=customer_actor_headers,
                )
                assert customer_cannot_enumerate_tenant_users.status_code == 403, (
                    customer_cannot_enumerate_tenant_users.text
                )
                customer_cannot_enumerate_tenant_roles = await client.get(
                    "/api/v1/tenant-admin/roles",
                    headers=customer_actor_headers,
                )
                assert customer_cannot_enumerate_tenant_roles.status_code == 403, (
                    customer_cannot_enumerate_tenant_roles.text
                )
                customer_cannot_change_user_status = await client.post(
                    f"/api/v1/tenant-admin/users/{customer_actor.id}/status",
                    headers=customer_actor_headers,
                    json={"is_active": True},
                )
                assert customer_cannot_change_user_status.status_code == 403, (
                    customer_cannot_change_user_status.text
                )
                customer_cannot_change_user_roles = await client.post(
                    f"/api/v1/tenant-admin/users/{customer_actor.id}/roles",
                    headers=customer_actor_headers,
                    json={"role_ids": [str(uuid.uuid4())]},
                )
                assert customer_cannot_change_user_roles.status_code == 403, (
                    customer_cannot_change_user_roles.text
                )
                customer_cannot_invite_tenant_user = await client.post(
                    "/api/v1/tenant-admin/invitations",
                    headers=customer_actor_headers,
                    json={
                        "email": f"customer-invite-{run_id}@example.com",
                        "role_ids": [str(uuid.uuid4())],
                    },
                )
                assert customer_cannot_invite_tenant_user.status_code == 403, (
                    customer_cannot_invite_tenant_user.text
                )
                customer_cannot_revoke_tenant_invitation = await client.post(
                    f"/api/v1/tenant-admin/invitations/{uuid.uuid4()}/revoke",
                    headers=customer_actor_headers,
                )
                assert customer_cannot_revoke_tenant_invitation.status_code == 403, (
                    customer_cannot_revoke_tenant_invitation.text
                )
                customer_vendor_grant_create = await client.post(
                    "/api/v1/edition/vendor/portal-access-grants",
                    headers=customer_actor_headers,
                    json={
                        "actor_user_id": str(customer_actor.id),
                        "target_tenant_id": str(target.id),
                        "reason": "Customer must not provision Vendor portal grants",
                    },
                )
                assert customer_vendor_grant_create.status_code == 403, customer_vendor_grant_create.text
                customer_escalation = await client.post(
                    "/api/v1/edition/reseller/portal-access-grants",
                    headers=customer_actor_headers,
                    json={"actor_user_id": str(customer_actor.id), "target_tenant_id": str(sibling.id), "reason": "Must be denied"},
                )
                assert customer_escalation.status_code == 403, customer_escalation.text
                # Customer identities must not activate or revoke grants, including
                # valid grants issued by the owning Vendor or Reseller.
                customer_vendor_grant_activate = await client.post(
                    f"/api/v1/edition/vendor/portal-access-grants/{grant_id}/activate",
                    headers=customer_actor_headers,
                )
                assert customer_vendor_grant_activate.status_code == 403, (
                    customer_vendor_grant_activate.text
                )
                customer_reseller_grant_activate = await client.post(
                    f"/api/v1/edition/reseller/portal-access-grants/{reseller_grant_id}/activate",
                    headers=customer_actor_headers,
                )
                assert customer_reseller_grant_activate.status_code == 403, (
                    customer_reseller_grant_activate.text
                )
                customer_vendor_grant_revoke = await client.delete(
                    f"/api/v1/edition/vendor/portal-access-grants/{grant_id}",
                    headers=customer_actor_headers,
                )
                assert customer_vendor_grant_revoke.status_code == 403, (
                    customer_vendor_grant_revoke.text
                )
                customer_reseller_grant_revoke = await client.delete(
                    f"/api/v1/edition/reseller/portal-access-grants/{reseller_grant_id}",
                    headers=customer_actor_headers,
                )
                assert customer_reseller_grant_revoke.status_code == 403, (
                    customer_reseller_grant_revoke.text
                )

                activated = await client.post(
                    f"/api/v1/edition/vendor/portal-access-grants/{grant_id}/activate",
                    headers=actor_headers,
                )
                assert activated.status_code == 200, activated.text
                context_refresh_token = activated.json()["data"]["refresh_token"]
                refreshed_context = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": context_refresh_token},
                )
                assert refreshed_context.status_code == 200, refreshed_context.text
                portal_token = refreshed_context.json()["data"]["access_token"]
                rotated_context_refresh = refreshed_context.json()["data"]["refresh_token"]
                portal_headers = {"Authorization": f"Bearer {portal_token}"}
                dispatched = await client.post(
                    f"/api/v1/workflows/{workflow_id}/runs", headers=portal_headers,
                    json={"input_data": {"origin": "vendor-portal"}},
                )
                assert dispatched.status_code == 201, dispatched.text
                workflow_run_id = dispatched.json()["data"]["id"]
                async with sessions() as session:
                    persisted_run = (await session.execute(
                        select(WorkflowRun).where(WorkflowRun.id == workflow_run_id)
                    )).scalar_one()
                    dispatch_message = (await session.execute(
                        select(OutboxMessage).where(
                            OutboxMessage.kind == "workflow.execute",
                            OutboxMessage.payload["workflow_run_id"].as_string() == workflow_run_id,
                        )
                    )).scalar_one()
                    assert persisted_run.tenant_id == target.id
                    assert dispatch_message.tenant_id == target.id
                    assert dispatch_message.payload["workflow_run_id"] == workflow_run_id

                me = await client.get("/api/v1/auth/me", headers=portal_headers)
                assert me.status_code == 200, me.text
                assert me.json()["data"]["tenant"]["id"] == str(target.id)
                assert me.json()["data"]["user"]["tenant_id"] == str(vendor.id)
                assert "employee.read" in me.json()["data"]["user"]["permissions"]

                target_audit = await client.get(
                    "/api/v1/operations/audit-logs", headers=portal_headers,
                )
                assert target_audit.status_code == 200, target_audit.text
                target_audit_actions = {item["action"] for item in target_audit.json()["data"]}
                assert "portal.acceptance.vendor-a.target" in target_audit_actions
                assert "portal.acceptance.vendor-a.sibling" not in target_audit_actions
                assert "portal.acceptance.vendor-b.target" not in target_audit_actions

                employees = await client.get("/api/v1/employees", headers=portal_headers)
                assert employees.status_code == 200, employees.text

                # Customer-dashboard career reads use AuditReadContext. Verify
                # that the effective portal tenant scopes both positive and
                # negative employee lookups across sibling reseller trees.
                target_career = await client.get(
                    f"/api/v1/customer-dashboard/employees/{target_dashboard_employee.id}/career",
                    headers=portal_headers,
                )
                assert target_career.status_code == 200, target_career.text
                assert target_career.json()["data"]["employee"]["id"] == str(target_dashboard_employee.id)
                sibling_career = await client.get(
                    f"/api/v1/customer-dashboard/employees/{sibling_dashboard_employee.id}/career",
                    headers=portal_headers,
                )
                assert sibling_career.status_code == 404, sibling_career.text

                # Usage reporting must follow the validated Reseller resource context,
                # not the Vendor actor or a sibling Reseller with much larger usage.
                usage_response = await client.get("/api/v1/usage/summary", headers=portal_headers)
                assert usage_response.status_code == 200, usage_response.text
                usage_data = usage_response.json()["data"]
                assert usage_data["calls"] == 1
                assert usage_data["prompt_tokens"] == 7
                assert usage_data["completion_tokens"] == 5
                assert usage_data["total_tokens"] == 12
                assert usage_data["cost_usd"] == 0.01

                optimization_contexts = []
                forecast_contexts = []

                async def portal_optimization(_db, *, tenant_id):
                    optimization_contexts.append(tenant_id)
                    return {
                        "period_start": datetime(2026, 11, 1, tzinfo=timezone.utc),
                        "plan": "business",
                        "usage": {"runs": 2, "tokens": 30},
                        "cost_usd": 0.12,
                        "successful_work_items": 2,
                        "cost_per_successful_work_item_usd": 0.06,
                        "budget": {
                            "state": "ok", "run_utilization": 0.1, "token_utilization": 0.2,
                            "remaining_runs": 18, "remaining_tokens": 970,
                        },
                        "optimization_actions": [],
                    }

                async def portal_forecast(_db, *, tenant_id):
                    forecast_contexts.append(tenant_id)
                    return {
                        "as_of": datetime(2026, 11, 12, tzinfo=timezone.utc),
                        "current_daily_cost_usd": 0.02, "baseline_daily_cost_usd": 0.01,
                        "anomaly": False, "anomaly_score": 1.0,
                        "month_to_date_cost_usd": 0.12, "projected_month_cost_usd": 0.31,
                        "baseline_days": 7, "actions": ["Continue observing spend."],
                    }

                monkeypatch.setattr(usage_api.optimization_service, "tenant_optimization_summary", portal_optimization)
                monkeypatch.setattr(usage_api.cost_anomaly_service, "tenant_cost_anomaly_forecast", portal_forecast)
                for portal_headers_for_usage, expected_tenant in (
                    (portal_headers, target.id),
                    (vendor_b_portal_headers, reseller_b.id),
                    (customer_portal_headers, customer_a.id),
                ):
                    optimization = await client.get(
                        "/api/v1/usage/optimization", headers=portal_headers_for_usage,
                    )
                    assert optimization.status_code == 200, optimization.text
                    assert optimization.json()["data"]["plan"] == "business"
                    forecast = await client.get(
                        "/api/v1/usage/cost-forecast", headers=portal_headers_for_usage,
                    )
                    assert forecast.status_code == 200, forecast.text
                    assert forecast.json()["data"]["baseline_days"] == 7
                    assert optimization_contexts[-1] == expected_tenant
                    assert forecast_contexts[-1] == expected_tenant

                # Revoking Vendor B's independent grant must invalidate its
                # already-issued portal token just as it does for Vendor A.
                vendor_b_revoked = await client.delete(
                    f"/api/v1/edition/vendor/portal-access-grants/{vendor_b_grant_id}",
                    headers=vendor_b_grantor_headers,
                )
                assert vendor_b_revoked.status_code == 200, vendor_b_revoked.text
                vendor_b_revoked_token = await client.get(
                    "/api/v1/auth/me", headers=vendor_b_portal_headers,
                )
                assert vendor_b_revoked_token.status_code == 403, vendor_b_revoked_token.text
                vendor_b_revoked_files = await client.get(
                    "/api/v1/files", headers=vendor_b_portal_headers,
                )
                assert vendor_b_revoked_files.status_code == 403, (
                    vendor_b_revoked_files.text
                )
                vendor_b_revoked_download = await client.get(
                    f"/api/v1/files/{vendor_b_file.id}/download",
                    headers=vendor_b_portal_headers,
                )
                assert vendor_b_revoked_download.status_code == 403, (
                    vendor_b_revoked_download.text
                )

                # Revoking a Reseller-to-Customer grant must invalidate the
                # already-issued Customer portal token immediately.
                reseller_customer_revoked = await client.delete(
                    f"/api/v1/edition/reseller/portal-access-grants/{reseller_grant_id}",
                    headers=reseller_grantor_headers,
                )
                assert reseller_customer_revoked.status_code == 200, reseller_customer_revoked.text
                reseller_customer_revoked_token = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {customer_portal_token}"},
                )
                assert reseller_customer_revoked_token.status_code == 403, (
                    reseller_customer_revoked_token.text
                )
                revoked_customer_invoice_export = await client.post(
                    f"/api/v1/invoices/{customer_invoice.id}/export-pdf",
                    headers=customer_portal_headers,
                )
                assert revoked_customer_invoice_export.status_code == 403, (
                    revoked_customer_invoice_export.text
                )
                revoked_customer_portal_files = await client.get(
                    "/api/v1/files",
                    headers=customer_portal_headers,
                )
                assert revoked_customer_portal_files.status_code == 403, (
                    revoked_customer_portal_files.text
                )
                revoked_customer_portal_download = await client.get(
                    f"/api/v1/files/{customer_file.id}/download",
                    headers={"Authorization": f"Bearer {customer_portal_token}"},
                )
                assert revoked_customer_portal_download.status_code == 403, (
                    revoked_customer_portal_download.text
                )

                # Invoice list, detail, and financial aggregates must use the
                # validated portal tenant, not the Vendor actor's home or sibling tenants.
                invoices = await client.get("/api/v1/invoices", headers=portal_headers)
                assert invoices.status_code == 200, invoices.text
                invoice_data = invoices.json()["data"]
                assert [item["id"] for item in invoice_data] == [str(target_invoice.id)]
                assert invoice_data[0]["number"] == target_invoice.number
                assert "Sibling Reseller Secret" not in str(invoice_data)
                assert "Vendor B Secret Customer" not in str(invoice_data)

                verification_record = await client.get(
                    f"/api/v1/test-center/runs/{target_test_run.id}/verification-record",
                    headers=portal_headers,
                )
                assert verification_record.status_code == 200, verification_record.text
                assert "attachment;" in verification_record.headers.get("content-disposition", "")
                verification_data = verification_record.json()
                assert verification_data["tenant_id"] == str(target.id)
                assert verification_data["run"]["id"] == str(target_test_run.id)
                assert verification_data["test_definition"]["name"] == "target private verification"
                assert [item["label"] for item in verification_data["artifacts"]] == [
                    "target-private-artifact"
                ]
                sibling_verification = await client.get(
                    f"/api/v1/test-center/runs/{sibling_test_run.id}/verification-record",
                    headers=portal_headers,
                )
                assert sibling_verification.status_code == 404, sibling_verification.text
                vendor_b_verification = await client.get(
                    f"/api/v1/test-center/runs/{vendor_b_test_run.id}/verification-record",
                    headers=portal_headers,
                )
                assert vendor_b_verification.status_code == 404, vendor_b_verification.text

                invoice_summary = await client.get("/api/v1/invoices/summary", headers=portal_headers)
                assert invoice_summary.status_code == 200, invoice_summary.text
                summary_data = invoice_summary.json()["data"]
                assert summary_data["total_invoices"] == 1
                assert summary_data["counts_by_status"] == {"paid": 1}
                assert summary_data["currency_breakdown"]["USD"]["collected"] == 120.0

                sibling_invoice_read = await client.get(
                    f"/api/v1/invoices/{sibling_invoice.id}", headers=portal_headers,
                )
                assert sibling_invoice_read.status_code == 404, sibling_invoice_read.text
                sibling_invoice_export = await client.post(
                    f"/api/v1/invoices/{sibling_invoice.id}/export-pdf", headers=portal_headers,
                )
                assert sibling_invoice_export.status_code == 404, sibling_invoice_export.text
                vendor_b_invoice_read = await client.get(
                    f"/api/v1/invoices/{vendor_b_invoice.id}", headers=portal_headers,
                )
                assert vendor_b_invoice_read.status_code == 404, vendor_b_invoice_read.text
                vendor_b_invoice_export_denied = await client.post(
                    f"/api/v1/invoices/{vendor_b_invoice.id}/export-pdf", headers=portal_headers,
                )
                assert vendor_b_invoice_export_denied.status_code == 404, vendor_b_invoice_export_denied.text
                target_pdf_export = await client.post(
                    f"/api/v1/invoices/{target_invoice.id}/export-pdf", headers=portal_headers,
                )
                assert target_pdf_export.status_code == 200, target_pdf_export.text
                target_pdf_id = target_pdf_export.json()["data"]["pdf_file_id"]
                async with sessions() as session:
                    target_pdf_row = await session.get(FileObject, uuid.UUID(target_pdf_id))
                    assert target_pdf_row is not None
                    assert target_pdf_row.tenant_id == target.id
                    assert target_pdf_row.uploaded_by == actor.id

                # Operations metrics and dead-letter payloads are tenant data too:
                # expose only the validated Reseller context, never sibling or Vendor B.
                operations_metrics = await client.get("/api/v1/operations/metrics", headers=portal_headers)
                assert operations_metrics.status_code == 200, operations_metrics.text
                metrics_data = operations_metrics.json()["data"]
                assert metrics_data["outbox"]["dead"] == 1
                assert metrics_data["workflow_runs_total"] == 1
                assert metrics_data["ai"]["calls"] == 1
                assert metrics_data["ai"]["tokens"] == 12
                assert metrics_data["ai"]["cost_usd"] == 0.01

                dead_letters = await client.get("/api/v1/operations/dead-letters", headers=portal_headers)
                assert dead_letters.status_code == 200, dead_letters.text
                dead_letter_data = dead_letters.json()["data"]
                assert [item["id"] for item in dead_letter_data] == [str(target_dead_letter.id)]
                assert dead_letter_data[0]["payload"]["private_marker"] == "target-reseller-dead-letter"
                assert "sibling-reseller-secret" not in str(dead_letter_data)
                assert "vendor-b-secret" not in str(dead_letter_data)

                sibling_replay = await client.post(
                    f"/api/v1/operations/dead-letters/{sibling_dead_letter.id}/replay",
                    headers=portal_headers,
                )
                assert sibling_replay.status_code == 404, sibling_replay.text
                vendor_b_replay = await client.post(
                    f"/api/v1/operations/dead-letters/{vendor_b_dead_letter.id}/replay",
                    headers=portal_headers,
                )
                assert vendor_b_replay.status_code == 404, vendor_b_replay.text
                target_replay = await client.post(
                    f"/api/v1/operations/dead-letters/{target_dead_letter.id}/replay",
                    headers=portal_headers,
                )
                assert target_replay.status_code == 200, target_replay.text
                assert target_replay.json()["data"]["status"] == "pending"

                # The live office view also aggregates employee identity and
                # presentation state. Stub only billing lookups so this test
                # isolates tenant-scoped office data from plan provisioning.
                async def portal_test_subscription(_db, *, tenant_id):
                    assert tenant_id == target.id
                    plan = SimpleNamespace(
                        code="business", name="Business", features={},
                        max_employees=20, max_workflows=25,
                        monthly_runs=2000, monthly_tokens=2_000_000,
                    )
                    return SimpleNamespace(plan=plan, status="active")

                async def portal_test_monthly_usage(_db, *, tenant_id, **_kwargs):
                    assert tenant_id == target.id
                    return {"calls": 0, "tokens": 0, "runs": 0, "employees": 1, "workflows": 0}

                monkeypatch.setattr(
                    customer_dashboard_service.billing_service,
                    "get_subscription", portal_test_subscription,
                )
                monkeypatch.setattr(
                    customer_dashboard_service.billing_service,
                    "monthly_usage", portal_test_monthly_usage,
                )
                office_response = await client.get(
                    "/api/v1/customer-dashboard/office", headers=portal_headers,
                )
                assert office_response.status_code == 200, office_response.text
                office_data = office_response.json()["data"]
                assert office_data["employee_count"] == 1
                assert [item["id"] for item in office_data["employees"]] == [
                    str(target_dashboard_employee.id)
                ]
                assert all(
                    item["name"] != sibling_dashboard_employee.name
                    for item in office_data["employees"]
                )

                # Aggregate dashboard metrics must resolve against the validated
                # Reseller context, not the Vendor actor or sibling Reseller.
                dashboard_response = await client.get(
                    "/api/v1/customer-dashboard", headers=portal_headers,
                )
                assert dashboard_response.status_code == 200, dashboard_response.text
                dashboard_data = dashboard_response.json()["data"]
                assert dashboard_data["employee_count"] == 1
                assert dashboard_data["active_employee_count"] == 1

                target_meeting_response = await client.get(
                    f"/api/v1/customer-dashboard/meetings/{target_meeting.id}",
                    headers=portal_headers,
                )
                assert target_meeting_response.status_code == 200, target_meeting_response.text
                target_meeting_data = target_meeting_response.json()["data"]
                assert target_meeting_data["meeting"]["id"] == str(target_meeting.id)
                assert [item["employee_id"] for item in target_meeting_data["participants"]] == [
                    str(target_dashboard_employee.id)
                ]
                assert all(item["employee_name"] != sibling_dashboard_employee.name
                           for item in target_meeting_data["participants"])
                sibling_meeting_response = await client.get(
                    f"/api/v1/customer-dashboard/meetings/{sibling_meeting.id}",
                    headers=portal_headers,
                )
                assert sibling_meeting_response.status_code == 404, sibling_meeting_response.text

                visible_files = await client.get("/api/v1/files", headers=portal_headers)
                assert visible_files.status_code == 200, visible_files.text
                assert str(target_file.id) in {item["id"] for item in visible_files.json()["data"]}
                # Exercise the real Report Employee tool handler with the validated
                # delegated portal tenant and authenticated Vendor actor context.
                report_source = await client.post(
                    "/api/v1/files",
                    headers=portal_headers,
                    files={"file": ("portal-report.csv", b"product,revenue,units\nA,120,2\nB,240,4\nC,180,3\n", "text/csv")},
                )
                assert report_source.status_code == 201, report_source.text
                report_source_id = report_source.json()["data"]["id"]
                from app.ai.tool_registry import registry
                from app.services import license_service

                async with sessions() as session:
                    async def allow_report_entitlement(_db, *, tenant_id, feature_code):
                        assert tenant_id == target.id
                        assert feature_code == registry.get("analyze_dataset").entitlement_code
                    with monkeypatch.context() as report_entitlement_override:
                        report_entitlement_override.setattr(license_service, "assert_feature_entitlement", allow_report_entitlement)
                        report_result = await registry.execute(
                            "analyze_dataset",
                            {"file_id": report_source_id},
                            permissions={"run.execute"},
                            allowed_tools={"analyze_dataset"},
                            db=session,
                            tenant_id=target.id,
                            actor_id=actor.id,
                        )
                    await session.commit()
                    report_artifacts = report_result["report_artifacts"]
                    report_artifact_ids = [
                        report_artifacts["pdf_file_id"],
                        report_artifacts["excel_file_id"],
                        *report_artifacts["chart_file_ids"],
                    ]
                    assert report_artifacts["chart_file_ids"], report_artifacts
                    report_rows = (await session.execute(
                        select(FileObject).where(
                            FileObject.id.in_([uuid.UUID(value) for value in report_artifact_ids])
                        )
                    )).scalars().all()
                    assert len(report_rows) == len(report_artifact_ids)
                    assert {row.tenant_id for row in report_rows} == {target.id}
                    assert {row.uploaded_by for row in report_rows} == {actor.id}
                    assert all(row.status == "active" for row in report_rows)
                    report_types = {row.content_type for row in report_rows}
                    assert "application/pdf" in report_types
                    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in report_types
                    assert "image/png" in report_types

                report_files = await client.get("/api/v1/files", headers=portal_headers)
                assert report_files.status_code == 200, report_files.text
                report_visible_ids = {item["id"] for item in report_files.json()["data"]}
                assert set(report_artifact_ids).issubset(report_visible_ids)
                for artifact_id in report_artifact_ids:
                    report_download = await client.get(
                        f"/api/v1/files/{artifact_id}/download", headers=portal_headers,
                    )
                    assert report_download.status_code == 200, report_download.text
                    assert report_download.content
                    sibling_report_read = await client.get(
                        f"/api/v1/files/{artifact_id}", headers=vendor_b_actor_headers,
                    )
                    assert sibling_report_read.status_code == 404, sibling_report_read.text
                    sibling_report_download = await client.get(
                        f"/api/v1/files/{artifact_id}/download", headers=vendor_b_actor_headers,
                    )
                    assert sibling_report_download.status_code == 404, sibling_report_download.text
                foreign_file = await client.get(f"/api/v1/files/{sibling_file.id}", headers=portal_headers)
                assert foreign_file.status_code == 404, foreign_file.text
                cross_vendor_file_response = await client.get(f"/api/v1/files/{cross_vendor_file.id}", headers=portal_headers)
                assert cross_vendor_file_response.status_code == 404, cross_vendor_file_response.text
                # Privacy exports must use the validated portal resource context;
                # a valid Vendor-to-Reseller grant cannot export a sibling tenant customer.
                target_customer_export = await client.get(
                    f"/api/v1/privacy/customers/{target_customer.id}/export", headers=portal_headers,
                )
                assert target_customer_export.status_code == 200, target_customer_export.text
                assert target_customer_export.json()["data"]["customer"]["id"] == str(target_customer.id)
                sibling_customer_export = await client.get(
                    f"/api/v1/privacy/customers/{sibling_customer.id}/export", headers=portal_headers,
                )
                assert sibling_customer_export.status_code == 404, sibling_customer_export.text
                cross_vendor_customer_export = await client.get(
                    f"/api/v1/privacy/customers/{cross_vendor_customer.id}/export", headers=portal_headers,
                )
                assert cross_vendor_customer_export.status_code == 404, cross_vendor_customer_export.text
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
                # Tenant notification destinations are private tenant-admin settings;
                # portal context must not read or mutate them even when the grant is valid.
                blocked_notification_read = await client.get(
                    "/api/v1/tenant-admin/customer-handoff-notification", headers=portal_headers,
                )
                assert blocked_notification_read.status_code == 403, blocked_notification_read.text
                blocked_notification_write = await client.put(
                    "/api/v1/tenant-admin/customer-handoff-notification",
                    headers=portal_headers,
                    json={"email": "attacker-controlled@example.com"},
                )
                assert blocked_notification_write.status_code == 403, blocked_notification_write.text
                blocked_billing = await client.get("/api/v1/billing/subscription", headers=portal_headers)
                assert blocked_billing.status_code == 403, blocked_billing.text

                revoked = await client.delete(
                    f"/api/v1/edition/vendor/portal-access-grants/{grant_id}",
                    headers=grantor_headers,
                )
                assert revoked.status_code == 200, revoked.text
                denied = await client.get("/api/v1/auth/me", headers=portal_headers)
                assert denied.status_code == 403, denied.text
                revoked_context_refresh = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": rotated_context_refresh},
                )
                assert revoked_context_refresh.status_code == 401, revoked_context_refresh.text
                revoked_vendor_invoice_export = await client.post(
                    f"/api/v1/invoices/{target_invoice.id}/export-pdf", headers=portal_headers,
                )
                assert revoked_vendor_invoice_export.status_code == 403, revoked_vendor_invoice_export.text
                revoked_vendor_portal_files = await client.get("/api/v1/files", headers=portal_headers)
                assert revoked_vendor_portal_files.status_code == 403, (
                    revoked_vendor_portal_files.text
                )

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
