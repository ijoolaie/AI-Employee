"""Real HTTP + PostgreSQL tests for commercial license boundaries.

Fail closed: only the dedicated aiep_license_test database is accepted.
This test deliberately leaves uniquely named rows and audit entries in that
isolated database; it does not delete or rewrite audit history.
"""

import hashlib
import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def _validated_database_url() -> str:
    raw = os.environ.get("COMMERCIAL_LICENSE_TEST_DATABASE_URL", "")
    if not raw:
        raise RuntimeError(
            "COMMERCIAL_LICENSE_TEST_DATABASE_URL is required; refusing to run."
        )

    parsed = make_url(raw)
    if (
        parsed.drivername != "postgresql+asyncpg"
        or parsed.database != "aiep_license_test"
        or not (
            parsed.host == "postgres"
            or (os.getenv("CI", "").lower() == "true" and parsed.host == "localhost")
        )
        or parsed.port != 5432
        or parsed.username != "aiep"
        or not parsed.password
    ):
        raise RuntimeError(
            "Refusing to run: URL must target aiep_license_test on "
            "the isolated Compose PostgreSQL service (or localhost in CI)."
        )
    return raw


@pytest.mark.asyncio
async def test_license_http_hierarchy_revocation_and_audit():
    database_url = _validated_database_url()

    # Import application modules only after validating the dedicated DB URL.
    from app.core.database import get_db
    from app.core.security import create_access_token
    from app.main import app
    from app.models.api_key import APIKey
    from app.models.audit_log import AuditLog
    from app.models.file import FileObject
    from app.models.license import CommercialLicense
    from app.models.role import Role
    from app.models.support_escalation import SupportEscalation
    from app.models.support_escalation_message import SupportEscalationMessage
    from app.models.support_escalation_message_attachment import SupportEscalationMessageAttachment
    from app.models.tenant import Tenant
    from app.models.user import User

    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    run_id = uuid.uuid4().hex
    vendor_a_id, vendor_b_id, reseller_a_id, reseller_b_id, customer_a_id, customer_b_id = (
        uuid.uuid4() for _ in range(6)
    )
    user_a_id, user_b_id, user_reseller_id, user_customer_id, user_vendor_superuser_id = (
        uuid.uuid4() for _ in range(5)
    )
    role_a_id, role_b_id = uuid.uuid4(), uuid.uuid4()
    escalation_id, message_id, file_id, attachment_id = (uuid.uuid4() for _ in range(4))
    api_key_secrets: dict[str, str] = {}

    async def override_get_db():
        async with sessions() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    missing = object()
    previous_override = app.dependency_overrides.get(get_db, missing)
    app.dependency_overrides[get_db] = override_get_db

    try:
        # Seed only new, uniquely named records in the dedicated test database.
        async with sessions() as session:
            vendor_a = Tenant(
                id=vendor_a_id, name=f"Vendor A {run_id}",
                slug=f"lic-vendor-a-{run_id}", tenant_kind="vendor", status="active",
            )
            vendor_b = Tenant(
                id=vendor_b_id, name=f"Vendor B {run_id}",
                slug=f"lic-vendor-b-{run_id}", tenant_kind="vendor", status="active",
            )
            reseller_a = Tenant(
                id=reseller_a_id, name=f"Reseller A {run_id}",
                slug=f"lic-reseller-a-{run_id}", tenant_kind="reseller",
                parent_tenant_id=vendor_a_id, status="active",
            )
            reseller_b = Tenant(
                id=reseller_b_id, name=f"Reseller B {run_id}",
                slug=f"lic-reseller-b-{run_id}", tenant_kind="reseller",
                parent_tenant_id=vendor_b_id, status="active",
            )
            customer_a = Tenant(
                id=customer_a_id, name=f"Customer A {run_id}",
                slug=f"lic-customer-a-{run_id}", tenant_kind="customer",
                parent_tenant_id=reseller_a_id, status="active",
            )
            customer_b = Tenant(
                id=customer_b_id, name=f"Customer B {run_id}",
                slug=f"lic-customer-b-{run_id}", tenant_kind="customer",
                parent_tenant_id=reseller_b_id, status="active",
            )
            role_a = Role(id=role_a_id, tenant_id=vendor_a_id, name="admin")
            role_b = Role(id=role_b_id, tenant_id=vendor_b_id, name="admin")

            # Persist tenant parents before children to satisfy the self-referencing FK.
            session.add_all([vendor_a, vendor_b])
            await session.commit()

            session.add_all([reseller_a, reseller_b])
            await session.commit()

            session.add_all([customer_a, customer_b])
            await session.commit()

            # Roles reference tenant rows, so insert them after the tenants.
            session.add_all([role_a, role_b])
            await session.commit()

            user_a = User(
                id=user_a_id, tenant_id=vendor_a_id,
                email=f"lic-vendor-a-{run_id}@example.test",
                password_hash="unused-test-hash", full_name="Test Vendor A Admin",
                is_active=True, is_superuser=False, is_platform_admin=False,
                auth_token_version=0,
            )
            user_b = User(
                id=user_b_id, tenant_id=vendor_b_id,
                email=f"lic-vendor-b-{run_id}@example.test",
                password_hash="unused-test-hash", full_name="Test Vendor B Admin",
                is_active=True, is_superuser=False, is_platform_admin=False,
                auth_token_version=0,
            )
            # Superuser owners are intentional here: the API key's explicit
            # scopes must still constrain access even when the owner is superuser.
            user_vendor_superuser = User(
                id=user_vendor_superuser_id, tenant_id=vendor_a_id,
                email=f"lic-vendor-superuser-{run_id}@example.test",
                password_hash="unused-test-hash", full_name="Test Vendor Superuser API Key Owner",
                is_active=True, is_superuser=True, is_platform_admin=False,
                auth_token_version=0,
            )
            user_reseller = User(
                id=user_reseller_id, tenant_id=reseller_a_id,
                email=f"lic-reseller-{run_id}@example.test",
                password_hash="unused-test-hash", full_name="Test Reseller API Key Owner",
                is_active=True, is_superuser=True, is_platform_admin=False,
                auth_token_version=0,
            )
            user_customer = User(
                id=user_customer_id, tenant_id=customer_a_id,
                email=f"lic-customer-{run_id}@example.test",
                password_hash="unused-test-hash", full_name="Test Customer API Key Owner",
                is_active=True, is_superuser=True, is_platform_admin=False,
                auth_token_version=0,
            )
            user_a.roles.append(role_a)
            user_b.roles.append(role_b)
            session.add_all([user_a, user_b, user_vendor_superuser, user_reseller, user_customer])
            await session.commit()

            def make_api_key(name: str, tenant_id, user_id, scopes):
                secret = f"aiep_live_test_{name}_{run_id}"
                api_key_secrets[name] = secret
                return APIKey(
                    tenant_id=tenant_id,
                    created_by=user_id,
                    name=f"Integration {name}",
                    key_prefix=secret[:20],
                    key_hash=hashlib.sha256(secret.encode("utf-8")).hexdigest(),
                    scopes=scopes,
                )

            session.add_all([
                make_api_key("vendor_read", vendor_a_id, user_a_id, ["edition.vendor.resellers.read"]),
                make_api_key("vendor_wrong", vendor_a_id, user_a_id, ["edition.vendor.tenants.read"]),
                make_api_key("vendor_legacy", vendor_a_id, user_a_id, None),
                make_api_key("vendor_superuser_wrong", vendor_a_id, user_vendor_superuser_id, ["edition.vendor.tenants.read"]),
                make_api_key("reseller_read", reseller_a_id, user_reseller_id, ["edition.reseller.customers.read"]),
                make_api_key("customer_support_read", customer_a_id, user_customer_id, ["edition.support.read"]),
                make_api_key(
                    "foreign_vendor_support_read",
                    vendor_b_id,
                    user_b_id,
                    ["edition.support.read", "edition.support.attachment.read"],
                ),
            ])
            session.add_all([
                SupportEscalation(
                    id=escalation_id,
                    from_tenant_id=customer_a_id,
                    to_tenant_id=reseller_a_id,
                    opened_by=user_customer_id,
                    subject=f"Isolation test {run_id}",
                    description="Integration-test support participant boundary",
                    status="open",
                    extra_data={},
                ),
                FileObject(
                    id=file_id,
                    tenant_id=customer_a_id,
                    uploaded_by=user_customer_id,
                    filename="support-boundary-test.txt",
                    content_type="text/plain",
                    size_bytes=4,
                    storage_key=f"test-only/{run_id}/support-boundary-test.txt",
                    status="active",
                ),
            ])
            await session.commit()
            session.add(SupportEscalationMessage(
                id=message_id,
                escalation_id=escalation_id,
                author_tenant_id=customer_a_id,
                author_user_id=user_customer_id,
                body="Boundary-test message",
            ))
            await session.commit()
            session.add(SupportEscalationMessageAttachment(
                id=attachment_id,
                message_id=message_id,
                file_id=file_id,
            ))
            await session.commit()

        token_a = create_access_token(
            subject=user_a_id, tenant_id=vendor_a_id,
            extra_claims={"auth_token_version": 0},
        )
        token_b = create_access_token(
            subject=user_b_id, tenant_id=vendor_b_id,
            extra_claims={"auth_token_version": 0},
        )
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}
        vendor_superuser_token = create_access_token(
            subject=user_vendor_superuser_id, tenant_id=vendor_a_id,
            extra_claims={"auth_token_version": 0},
        )
        vendor_superuser_bearer = {
            "Authorization": f"Bearer {vendor_superuser_token}"
        }
        base = "/api/v1/edition/licenses"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            edition_base = "/api/v1/edition"
            vendor_read_headers = {"X-API-Key": api_key_secrets["vendor_read"]}
            vendor_wrong_headers = {"X-API-Key": api_key_secrets["vendor_wrong"]}
            vendor_legacy_headers = {"X-API-Key": api_key_secrets["vendor_legacy"]}
            vendor_superuser_wrong_headers = {
                "X-API-Key": api_key_secrets["vendor_superuser_wrong"]
            }
            reseller_read_headers = {"X-API-Key": api_key_secrets["reseller_read"]}
            customer_read_headers = {
                "X-API-Key": api_key_secrets["customer_support_read"]
            }

            # API-key creation rejects unknown and cross-edition scopes.
            unknown_scope_key = await client.post(
                "/api/v1/api-keys",
                headers=vendor_superuser_bearer,
                json={"name": "invalid unknown scope", "scopes": ["*"]},
            )
            assert unknown_scope_key.status_code == 400, unknown_scope_key.text
            cross_edition_key = await client.post(
                "/api/v1/api-keys",
                headers=vendor_superuser_bearer,
                json={
                    "name": "invalid cross edition scope",
                    "scopes": ["edition.reseller.customers.read"],
                },
            )
            assert cross_edition_key.status_code == 400, cross_edition_key.text
            valid_edition_key = await client.post(
                "/api/v1/api-keys",
                headers=vendor_superuser_bearer,
                json={
                    "name": "valid edition scope",
                    "scopes": ["edition.vendor.resellers.read"],
                },
            )
            assert valid_edition_key.status_code == 201, valid_edition_key.text

            # API-key scopes are enforced by the real HTTP dependency chain.
            vendor_read = await client.get(
                f"{edition_base}/vendor/resellers", headers=vendor_read_headers
            )
            assert vendor_read.status_code == 200, vendor_read.text

            vendor_wrong = await client.get(
                f"{edition_base}/vendor/resellers", headers=vendor_wrong_headers
            )
            assert vendor_wrong.status_code == 403, vendor_wrong.text

            # Legacy NULL-scope keys and superuser keys with the wrong scope fail closed.
            vendor_legacy = await client.get(
                f"{edition_base}/vendor/resellers", headers=vendor_legacy_headers
            )
            assert vendor_legacy.status_code == 403, vendor_legacy.text
            vendor_superuser_wrong = await client.get(
                f"{edition_base}/vendor/resellers",
                headers=vendor_superuser_wrong_headers,
            )
            assert vendor_superuser_wrong.status_code == 403, vendor_superuser_wrong.text

            reseller_read = await client.get(
                f"{edition_base}/reseller/customers", headers=reseller_read_headers
            )
            assert reseller_read.status_code == 200, reseller_read.text

            customer_read = await client.get(
                f"{edition_base}/support/escalations", headers=customer_read_headers
            )
            assert customer_read.status_code == 200, customer_read.text

            # Only participants may read a support escalation's messages.
            participant_messages = await client.get(
                f"{edition_base}/support/escalations/{escalation_id}/messages",
                headers=customer_read_headers,
            )
            assert participant_messages.status_code == 200, participant_messages.text
            foreign_messages = await client.get(
                f"{edition_base}/vendor/support/escalations/{escalation_id}/messages",
                headers={"X-API-Key": api_key_secrets["foreign_vendor_support_read"]},
            )
            assert foreign_messages.status_code == 404, foreign_messages.text
            assert len(participant_messages.json()["data"]) == 1

            foreign_attachment = await client.get(
                f"{edition_base}/vendor/support/escalations/{escalation_id}/messages/{message_id}/attachments/{attachment_id}/download",
                headers={"X-API-Key": api_key_secrets["foreign_vendor_support_read"]},
            )
            assert foreign_attachment.status_code == 404, foreign_attachment.text

            # Authentication must be enforced by the actual HTTP dependency chain.
            unauthenticated = await client.post(
                f"{base}/vendor/tenants/{customer_a_id}",
                json={"feature_codes": ["tool:test_feature"]},
            )
            assert unauthenticated.status_code == 401, unauthenticated.text

            # Vendor A cannot issue a license to a tenant under Vendor B.
            foreign_issue = await client.post(
                f"{base}/vendor/tenants/{customer_b_id}",
                headers=headers_a,
                json={"feature_codes": ["tool:test_feature"]},
            )
            assert foreign_issue.status_code == 409, foreign_issue.text

            # Valid issue by Vendor A to a customer in its own hierarchy.
            issue_a = await client.post(
                f"{base}/vendor/tenants/{customer_a_id}",
                headers=headers_a,
                json={
                    "expires_in_days": 30,
                    "feature_codes": ["tool:test_feature", "tool:test_feature"],
                    "metadata": {"test_run": run_id},
                },
            )
            assert issue_a.status_code == 201, issue_a.text
            issued_a = issue_a.json()["data"]
            license_a_id = uuid.UUID(issued_a["id"])
            assert issued_a["tenant_id"] == str(customer_a_id)
            assert issued_a["issuer_tenant_id"] == str(vendor_a_id)
            assert issued_a["status"] == "active"
            assert issued_a["feature_codes"] == ["tool:test_feature"]

            # Vendor B issues its own license. Vendor A must not revoke it.
            issue_b = await client.post(
                f"{base}/vendor/tenants/{customer_b_id}",
                headers=headers_b,
                json={
                    "expires_in_days": 30,
                    "feature_codes": ["tool:other_feature"],
                    "metadata": {"test_run": run_id},
                },
            )
            assert issue_b.status_code == 201, issue_b.text
            license_b_id = uuid.UUID(issue_b.json()["data"]["id"])

            foreign_revoke = await client.post(
                f"{base}/vendor/{license_b_id}/revoke",
                headers=headers_a,
                json={"reason": "Unauthorized issuer test"},
            )
            assert foreign_revoke.status_code == 409, foreign_revoke.text

            # The actual issuer can revoke its license.
            revoke_b = await client.post(
                f"{base}/vendor/{license_b_id}/revoke",
                headers=headers_b,
                json={"reason": f"Integration test {run_id}"},
            )
            assert revoke_b.status_code == 200, revoke_b.text
            revoked = revoke_b.json()["data"]
            assert revoked["status"] == "revoked"
            assert revoked["revocation_reason"] == f"Integration test {run_id}"
            assert revoked["revoked_at"] is not None

        # Verify persistence using a separate PostgreSQL session.
        async with sessions() as session:
            persisted_a = await session.get(CommercialLicense, license_a_id)
            persisted_b = await session.get(CommercialLicense, license_b_id)
            assert persisted_a is not None
            assert persisted_a.status == "active"
            assert persisted_a.issuer_tenant_id == vendor_a_id
            assert persisted_a.feature_codes == ["tool:test_feature"]
            assert persisted_b is not None
            assert persisted_b.status == "revoked"
            assert persisted_b.revocation_reason == f"Integration test {run_id}"
            assert persisted_b.revoked_at is not None

            issue_a_audit = (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.action == "license.issued",
                        AuditLog.resource_id == str(license_a_id),
                    )
                )
            ).scalars().first()
            revoke_b_audit = (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.action == "license.revoked",
                        AuditLog.resource_id == str(license_b_id),
                    )
                )
            ).scalars().first()
            assert issue_a_audit is not None
            assert revoke_b_audit is not None

    finally:
        if previous_override is missing:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override
        await engine.dispose()
