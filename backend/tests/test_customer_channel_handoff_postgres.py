"""PostgreSQL-backed tenant-isolation regression for customer handoff.

This test only runs against the dedicated support_test database. It skips when
that explicit test database URL is not configured and fails closed if the URL
points anywhere else.
"""

import os
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def _support_test_database_url() -> str:
    url = os.environ.get("SUPPORT_TEST_DATABASE_URL")
    if not url:
        pytest.skip("SUPPORT_TEST_DATABASE_URL is not configured")
    parsed = make_url(url)
    if (
        parsed.drivername != "postgresql+asyncpg"
        or parsed.host not in {"127.0.0.1", "localhost"}
        or parsed.port not in {5432, 15433}
        or parsed.database != "support_test"
        or parsed.username not in {"support_test_user", "aiep"}
        or not parsed.password
    ):
        raise RuntimeError(
            "Refusing to run customer handoff integration test outside the "
            "dedicated local support_test database."
        )
    return url


@pytest.mark.asyncio
async def test_handoff_is_persisted_and_assignee_is_tenant_scoped_in_postgres(monkeypatch):
    from sqlalchemy import select

    from app.core.exceptions import NotFoundError
    from app.models.customer_channel import CustomerChannel
    from app.models.conversation import CustomerConversation, CustomerMessage
    from app.models.employee import Employee
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.outbox import OutboxMessage
    from app.services import customer_channel_service
    from app.services.customer_channel_service import _hash_token, send_message, update_handoff

    # Exercise the configured notification path without sending real email.
    monkeypatch.setattr(
        customer_channel_service,
        "get_settings",
        lambda: SimpleNamespace(
            smtp_host="smtp.example.test",
            smtp_from_email="support@example.test",
        ),
    )

    engine = create_async_engine(_support_test_database_url(), poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex

    try:
        async with sessions() as session:
            # Keep the fixture creation ordered explicitly: some model mappings
            # do not declare ORM relationships, so flush each FK dependency.
            async with session.begin():
                tenant_a = Tenant(
                    id=uuid.uuid4(), name=f"Handoff tenant A {suffix}",
                    slug=f"handoff-a-{suffix}", tenant_kind="customer", status="active",
                    settings={"customer_handoff_notification_email": "ops@example.test"},
                )
                tenant_b = Tenant(
                    id=uuid.uuid4(), name=f"Handoff tenant B {suffix}",
                    slug=f"handoff-b-{suffix}", tenant_kind="customer", status="active",
                )
                session.add_all([tenant_a, tenant_b])
                await session.flush()

                employee = Employee(
                    id=uuid.uuid4(), tenant_id=tenant_a.id,
                    slug=f"handoff-agent-{suffix}", name="Handoff test agent",
                    kind="custom", is_active=True,
                )
                same_tenant_user = User(
                    id=uuid.uuid4(), tenant_id=tenant_a.id,
                    email=f"handoff-a-{suffix}@example.test",
                    password_hash="test-only-not-used", full_name="Tenant A agent",
                    is_active=True, is_superuser=False, is_platform_admin=False,
                    auth_token_version=0,
                )
                foreign_tenant_user = User(
                    id=uuid.uuid4(), tenant_id=tenant_b.id,
                    email=f"handoff-b-{suffix}@example.test",
                    password_hash="test-only-not-used", full_name="Tenant B agent",
                    is_active=True, is_superuser=False, is_platform_admin=False,
                    auth_token_version=0,
                )
                session.add_all([employee, same_tenant_user, foreign_tenant_user])
                await session.flush()

                channel = CustomerChannel(
                    id=uuid.uuid4(), tenant_id=tenant_a.id, employee_id=employee.id,
                    name="PostgreSQL handoff test", channel_type="web_widget",
                    public_key=f"pk_handoff_{suffix}", config={}, is_active=True,
                )
                session.add(channel)
                await session.flush()

                handoff_token = f"handoff-token-{suffix}"
                conversation = CustomerConversation(
                    id=uuid.uuid4(), tenant_id=tenant_a.id,
                    employee_id=employee.id, channel_id=channel.id,
                    customer_token_hash=_hash_token(handoff_token), customer_name="Synthetic customer",
                    status="open", handoff_requested=False,
                )
                session.add(conversation)
                await session.flush()

                with pytest.raises(NotFoundError, match="Assigned user not found"):
                    await update_handoff(
                        session, tenant_id=tenant_a.id,
                        conversation_id=conversation.id, requested=True,
                        assigned_user_id=foreign_tenant_user.id,
                    )
                assert conversation.handoff_requested is False
                assert conversation.assigned_user_id is None
                assert conversation.status == "open"

                updated = await update_handoff(
                    session, tenant_id=tenant_a.id,
                    conversation_id=conversation.id, requested=True,
                    assigned_user_id=same_tenant_user.id,
                )
                assert updated.id == conversation.id
                assert updated.handoff_requested is True
                assert updated.assigned_user_id == same_tenant_user.id
                assert updated.status == "human"

                persisted = (
                    await session.execute(
                        select(CustomerConversation).where(
                            CustomerConversation.id == conversation.id,
                            CustomerConversation.tenant_id == tenant_a.id,
                        )
                    )
                ).scalar_one()
                assert persisted.handoff_requested is True
                assert persisted.assigned_user_id == same_tenant_user.id
                assert persisted.status == "human"

                # Exercise the public customer-message path, not just the staff toggle.
                conversation.handoff_requested = False
                conversation.assigned_user_id = None
                conversation.status = "open"
                await session.flush()
                request_text = "I want to talk to a human"
                routed_conversation, run = await send_message(
                    session,
                    conversation_id=conversation.id,
                    token=handoff_token,
                    content=request_text,
                )
                assert run is None
                assert routed_conversation.handoff_requested is True
                assert routed_conversation.status == "human"
                assert routed_conversation.assigned_user_id is None
                saved_messages = list((await session.execute(
                    select(CustomerMessage).where(
                        CustomerMessage.conversation_id == conversation.id,
                        CustomerMessage.tenant_id == tenant_a.id,
                    )
                )).scalars().all())
                assert any(item.role == "user" and item.content == request_text for item in saved_messages)
                assert any(
                    item.role == "assistant" and "recorded" in item.content
                    for item in saved_messages
                )

                # The notification is durable in the same transaction as the
                # handoff state transition and remains tenant-scoped/deduplicated.
                outbox_rows = list((await session.execute(
                    select(OutboxMessage).where(
                        OutboxMessage.tenant_id == tenant_a.id,
                        OutboxMessage.dedupe_key == f"customer-handoff:{conversation.id}",
                    )
                )).scalars().all())
                assert len(outbox_rows) == 1
                outbox_row = outbox_rows[0]
                assert outbox_row.kind == "email.send"
                assert outbox_row.status == "pending"
                assert outbox_row.payload["to"] == ["ops@example.test"]
                assert str(tenant_a.id) in outbox_row.payload["body"]
                assert str(conversation.id) in outbox_row.payload["body"]
                assert str(channel.id) in outbox_row.payload["body"]

                # Re-enqueuing the same logical handoff must return the existing
                # row instead of creating a second notification.
                from app.services import outbox_service
                duplicate = await outbox_service.enqueue(
                    session,
                    tenant_id=tenant_a.id,
                    kind="email.send",
                    dedupe_key=f"customer-handoff:{conversation.id}",
                    payload={
                        "to": ["ops@example.test"],
                        "subject": "Duplicate should be deduplicated",
                        "body": "synthetic test",
                    },
                )
                assert duplicate.id == outbox_row.id
                duplicate_count = (
                    await session.execute(
                        select(OutboxMessage.id).where(
                            OutboxMessage.tenant_id == tenant_a.id,
                            OutboxMessage.dedupe_key == f"customer-handoff:{conversation.id}",
                        )
                    )
                ).all()
                assert len(duplicate_count) == 1

                # The same dedupe key in another tenant must not resolve to
                # tenant A's notification or suppress tenant B's own handoff.
                other_tenant = await outbox_service.enqueue(
                    session,
                    tenant_id=tenant_b.id,
                    kind="email.send",
                    dedupe_key=f"customer-handoff:{conversation.id}",
                    payload={
                        "to": ["ops@example.test"],
                        "subject": "Tenant B handoff",
                        "body": f"tenant_id={tenant_b.id}",
                    },
                )
                assert other_tenant.id != outbox_row.id
                assert other_tenant.tenant_id == tenant_b.id
                tenant_rows = (
                    await session.execute(
                        select(OutboxMessage.id).where(
                            OutboxMessage.dedupe_key == f"customer-handoff:{conversation.id}",
                        )
                    )
                ).all()
                assert len(tenant_rows) == 2
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_handoff_outbox_retry_and_dead_letter_states_persist_in_postgres(monkeypatch):
    """Verify retry/dead-letter transitions survive PostgreSQL commits."""
    from sqlalchemy import select

    from app.core import config
    from app.models.outbox import OutboxMessage
    from app.services.outbox_service import mark_retry

    def settings():
        return SimpleNamespace(outbox_max_attempts=2)

    monkeypatch.setattr(config, "get_settings", settings)
    engine = create_async_engine(_support_test_database_url(), poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex
    row_id = uuid.uuid4()
    try:
        async with sessions() as session:
            async with session.begin():
                row = OutboxMessage(
                    id=row_id,
                    tenant_id=uuid.uuid4(),
                    kind="email.send",
                    dedupe_key=f"handoff-retry-test:{suffix}",
                    payload={"to": ["ops@example.test"], "subject": "synthetic", "body": "synthetic"},
                    status="pending",
                    attempts=1,
                )
                session.add(row)
                await session.flush()
                await mark_retry(session, row, "synthetic temporary SMTP failure", delay_seconds=1)
                assert row.status == "pending"
                assert row.dead_at is None
                assert "synthetic temporary SMTP failure" in row.last_error

        async with sessions() as session:
            persisted = (await session.execute(
                select(OutboxMessage).where(OutboxMessage.id == row_id)
            )).scalar_one()
            assert persisted.status == "pending"
            assert persisted.attempts == 1
            assert persisted.last_error == "synthetic temporary SMTP failure"
            assert persisted.available_at is not None

            persisted.attempts = 2
            await mark_retry(session, persisted, "synthetic exhausted retries", delay_seconds=1)
            await session.commit()

        async with sessions() as session:
            dead = (await session.execute(
                select(OutboxMessage).where(OutboxMessage.id == row_id)
            )).scalar_one()
            assert dead.status == "dead"
            assert dead.dead_at is not None
            assert dead.last_error == "synthetic exhausted retries"
    finally:
        await engine.dispose()

