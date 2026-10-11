"""Real PostgreSQL + HTTP API regression test for support escalation persistence."""

import asyncio
import os
import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from httpx import ASGITransport, AsyncClient


def _validated_test_urls() -> tuple[str, str]:
    """Fail closed unless both URLs target the dedicated local support_test database."""
    async_url = os.environ.get("SUPPORT_TEST_DATABASE_URL") or os.environ.get(
        "DATABASE_URL", ""
    )
    sync_url = os.environ.get("SUPPORT_TEST_DATABASE_URL_SYNC") or os.environ.get(
        "DATABASE_URL_SYNC", ""
    )
    if not async_url or not sync_url:
        raise RuntimeError("Test database URLs are required; refusing to run.")

    async_parsed = make_url(async_url)
    sync_parsed = make_url(sync_url)

    allowed_hosts = {"127.0.0.1", "localhost"}
    allowed_ports = {5432, 15433}
    allowed_usernames = {"support_test_user", "aiep"}
    for label, parsed, driver in (
        ("SUPPORT_TEST_DATABASE_URL", async_parsed, "postgresql+asyncpg"),
        ("SUPPORT_TEST_DATABASE_URL_SYNC", sync_parsed, "postgresql+psycopg2"),
    ):
        if (
            parsed.drivername != driver
            or parsed.username not in allowed_usernames
            or parsed.host not in allowed_hosts
            or parsed.port not in allowed_ports
            or parsed.database != "support_test"
            or not parsed.password
        ):
            raise RuntimeError(
                f"{label} does not point to the dedicated local support_test database; refusing to run."
            )

    if (
        async_parsed.username != sync_parsed.username
        or async_parsed.host != sync_parsed.host
        or async_parsed.port != sync_parsed.port
        or async_parsed.database != sync_parsed.database
    ):
        raise RuntimeError("Async and sync test URLs must target the same database.")

    return async_url, sync_url


@pytest.mark.asyncio
async def test_reseller_escalation_and_messages_persist_and_are_tenant_isolated(monkeypatch):
    async_url, _ = _validated_test_urls()

    # Import the application only after validating the test DB environment.
    from app.core.database import get_db
    from app.core.security import create_access_token
    from app.main import app
    from app.api.v1 import edition_control
    from app.models.file import FileObject
    from app.models.role import Role
    from app.models.support_escalation import SupportEscalation
    from app.models.support_escalation_message import SupportEscalationMessage
    from app.models.support_escalation_message_attachment import SupportEscalationMessageAttachment
    from app.models.tenant import Tenant
    from app.models.user import User

    engine = create_async_engine(async_url, poolclass=NullPool)
    sessions = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    run_id = uuid.uuid4().hex
    vendor_id = uuid.uuid4()
    source_tenant_id = uuid.uuid4()
    unrelated_tenant_id = uuid.uuid4()
    source_user_id = uuid.uuid4()
    unrelated_user_id = uuid.uuid4()
    source_role_id = uuid.uuid4()
    unrelated_role_id = uuid.uuid4()

    async def override_get_db() -> AsyncIterator:
        async with sessions() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    missing_override = object()
    previous_get_db_override = app.dependency_overrides.get(
        get_db, missing_override
    )
    app.dependency_overrides[get_db] = override_get_db

    try:
        # Seed only uniquely named records in the verified test database.
        async with sessions() as session:
            vendor = Tenant(
                id=vendor_id,
                name=f"Test vendor {run_id}",
                slug=f"pgtest-vendor-{run_id}",
                tenant_kind="vendor",
                status="active",
            )
            source_tenant = Tenant(
                id=source_tenant_id,
                name=f"Test source reseller {run_id}",
                slug=f"pgtest-source-{run_id}",
                tenant_kind="reseller",
                parent_tenant_id=vendor_id,
                status="active",
            )
            unrelated_tenant = Tenant(
                id=unrelated_tenant_id,
                name=f"Test unrelated reseller {run_id}",
                slug=f"pgtest-unrelated-{run_id}",
                tenant_kind="reseller",
                parent_tenant_id=vendor_id,
                status="active",
            )
            source_role = Role(
                id=source_role_id,
                tenant_id=source_tenant_id,
                name="admin",
            )
            unrelated_role = Role(
                id=unrelated_role_id,
                tenant_id=unrelated_tenant_id,
                name="admin",
            )
            source_user = User(
                id=source_user_id,
                tenant_id=source_tenant_id,
                email=f"source-{run_id}@example.test",
                password_hash="not-used-by-this-test",
                full_name="Postgres Test Source Admin",
                is_active=True,
                is_superuser=False,
                is_platform_admin=False,
                auth_token_version=0,
            )
            unrelated_user = User(
                id=unrelated_user_id,
                tenant_id=unrelated_tenant_id,
                email=f"unrelated-{run_id}@example.test",
                password_hash="not-used-by-this-test",
                full_name="Postgres Test Unrelated Admin",
                is_active=True,
                is_superuser=False,
                is_platform_admin=False,
                auth_token_version=0,
            )
            source_user.roles.append(source_role)
            unrelated_user.roles.append(unrelated_role)
            race_file_id = uuid.uuid4()
            race_file = FileObject(
                id=race_file_id,
                tenant_id=source_tenant_id,
                uploaded_by=source_user_id,
                filename="concurrent-report.pdf",
                content_type="application/pdf",
                size_bytes=128,
                storage_key=f"{source_tenant_id}/pgtest/{run_id}/concurrent-report.pdf",
                status="active",
            )

            session.add_all(
                [
                    vendor,
                    source_tenant,
                    unrelated_tenant,
                    source_role,
                    unrelated_role,
                    source_user,
                    unrelated_user,
                ]
            )
            # Commit FK parents first: FileObject has FK columns but no ORM
            # relationship that guarantees unit-of-work insert ordering.
            await session.commit()
            session.add(race_file)
            await session.commit()

        source_token = create_access_token(
            subject=source_user_id,
            tenant_id=source_tenant_id,
            extra_claims={"auth_token_version": 0},
        )
        unrelated_token = create_access_token(
            subject=unrelated_user_id,
            tenant_id=unrelated_tenant_id,
            extra_claims={"auth_token_version": 0},
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            source_headers = {"Authorization": f"Bearer {source_token}"}
            unrelated_headers = {"Authorization": f"Bearer {unrelated_token}"}
            base = "/api/v1/edition/reseller/support/escalations"

            # 1. Create an escalation through the actual HTTP API.
            create_response = await client.post(
                base,
                headers=source_headers,
                json={
                    "subject": f"PostgreSQL persistence {run_id}",
                    "description": "Verify that this escalation is committed to PostgreSQL.",
                },
            )
            assert create_response.status_code == 201, create_response.text
            escalation_data = create_response.json()["data"]
            escalation_id = uuid.UUID(escalation_data["id"])
            assert escalation_data["from_tenant_id"] == str(source_tenant_id)
            assert escalation_data["to_tenant_id"] == str(vendor_id)

            # 2. Create a message through a separate HTTP request.
            messages_url = f"{base}/{escalation_id}/messages"
            message_body = f"Persist this support reply {run_id}"
            message_response = await client.post(
                messages_url,
                headers=source_headers,
                json={"body": message_body},
            )
            assert message_response.status_code == 201, message_response.text
            message_data = message_response.json()["data"]
            message_id = uuid.UUID(message_data["id"])
            assert message_data["escalation_id"] == str(escalation_id)
            assert message_data["body"] == message_body

            # 3. Read through a new API request/session and verify both records.
            read_response = await client.get(messages_url, headers=source_headers)
            assert read_response.status_code == 200, read_response.text
            returned_messages = read_response.json()["data"]
            persisted_message = next(
                item for item in returned_messages if item["id"] == str(message_id)
            )
            assert persisted_message["body"] == message_body
            assert persisted_message["escalation_id"] == str(escalation_id)

            sent_response = await client.get(
                f"{base}/sent",
                headers=source_headers,
            )
            assert sent_response.status_code == 200, sent_response.text
            assert any(
                item["id"] == str(escalation_id)
                for item in sent_response.json()["data"]
            )

            # 4. Verify persistence independently using a fresh database session.
            async with sessions() as verification_session:
                persisted_escalation = await verification_session.get(
                    SupportEscalation, escalation_id
                )
                persisted_message_row = await verification_session.get(
                    SupportEscalationMessage, message_id
                )
                assert persisted_escalation is not None
                assert persisted_escalation.from_tenant_id == source_tenant_id
                assert persisted_escalation.to_tenant_id == vendor_id
                assert persisted_message_row is not None
                assert persisted_message_row.escalation_id == escalation_id
                assert persisted_message_row.body == message_body

            # 5. An unrelated tenant must not see the escalation in its sent list.
            unrelated_sent = await client.get(
                f"{base}/sent",
                headers=unrelated_headers,
            )
            assert unrelated_sent.status_code == 200, unrelated_sent.text
            assert all(
                item["id"] != str(escalation_id)
                for item in unrelated_sent.json()["data"]
            )

            # Reading the foreign message thread must return 404, not auth failure.
            foreign_messages = await client.get(
                messages_url,
                headers=unrelated_headers,
            )
            assert foreign_messages.status_code == 404, foreign_messages.text

            # The status endpoint also scopes by recipient tenant and must hide it.
            foreign_status = await client.patch(
                f"{base}/{escalation_id}/status",
                headers=unrelated_headers,
                json={"status": "in_progress"},
            )
            assert foreign_status.status_code == 404, foreign_status.text

            # 6. Force two real HTTP requests past the attachment pre-check before
            # either request can insert its link. PostgreSQL must allow exactly one.
            race_bodies = [
                f"Concurrent attachment contender A {run_id}",
                f"Concurrent attachment contender B {run_id}",
            ]
            # Synchronize at the service boundary, not by matching generated SQL.
            # SQL-text matching was brittle and could leave the test waiting forever.
            original_create_message = edition_control._create_support_escalation_message
            race_barrier = asyncio.Barrier(2)

            async def synchronized_create_message(escalation_id, payload, ctx, db):
                if payload.attachment_file_ids:
                    await asyncio.wait_for(race_barrier.wait(), timeout=10)
                return await original_create_message(escalation_id, payload, ctx, db)

            monkeypatch.setattr(edition_control, "_create_support_escalation_message", synchronized_create_message)
            try:
                race_responses = await asyncio.wait_for(
                    asyncio.gather(
                        client.post(
                            messages_url,
                            headers=source_headers,
                            json={"body": race_bodies[0], "attachment_file_ids": [str(race_file_id)]},
                        ),
                        client.post(
                            messages_url,
                            headers=source_headers,
                            json={"body": race_bodies[1], "attachment_file_ids": [str(race_file_id)]},
                        ),
                    ),
                    timeout=20,
                )
            finally:
                monkeypatch.setattr(edition_control, "_create_support_escalation_message", original_create_message)

            assert sorted(response.status_code for response in race_responses) == [201, 409], [
                (response.status_code, response.text) for response in race_responses
            ]
            conflict_response = next(response for response in race_responses if response.status_code == 409)
            assert conflict_response.json()["detail"] == "A file can only be attached to one support message"

            # The losing request must roll back its message as well as its attachment.
            async with sessions() as verification_session:
                attachment_count = await verification_session.scalar(
                    select(func.count())
                    .select_from(SupportEscalationMessageAttachment)
                    .where(SupportEscalationMessageAttachment.file_id == race_file_id)
                )
                race_messages = (
                    await verification_session.execute(
                        select(SupportEscalationMessage).where(
                            SupportEscalationMessage.body.in_(race_bodies)
                        )
                    )
                ).scalars().all()
                assert attachment_count == 1
                assert len(race_messages) == 1
                assert race_messages[0].body in race_bodies

    finally:
        if previous_get_db_override is missing_override:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_get_db_override
        await engine.dispose()
