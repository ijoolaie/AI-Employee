"""PostgreSQL tests for tenant-safe acknowledgement of human handoffs.

Only the dedicated local support_test database is accepted; no real email is sent.
"""
import os
import uuid

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
        raise RuntimeError("Refusing to run handoff acknowledgement test outside support_test")
    return url


@pytest.mark.asyncio
async def test_handoff_acknowledgement_claims_unassigned_conversation_and_is_tenant_scoped():
    from app.core.exceptions import ConflictError, NotFoundError
    from app.models.conversation import CustomerConversation
    from app.models.customer_channel import CustomerChannel
    from app.models.employee import Employee
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.services.customer_channel_service import acknowledge_handoff, update_handoff

    engine = create_async_engine(_support_test_database_url(), poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex
    try:
        async with sessions() as session:
            async with session.begin():
                tenant_a = Tenant(
                    id=uuid.uuid4(), name=f"Ack tenant A {suffix}", slug=f"ack-a-{suffix}",
                    tenant_kind="customer", status="active",
                )
                tenant_b = Tenant(
                    id=uuid.uuid4(), name=f"Ack tenant B {suffix}", slug=f"ack-b-{suffix}",
                    tenant_kind="customer", status="active",
                )
                session.add_all([tenant_a, tenant_b])
                await session.flush()

                employee = Employee(
                    id=uuid.uuid4(), tenant_id=tenant_a.id, slug=f"ack-agent-{suffix}",
                    name="Ack test agent", kind="custom", is_active=True,
                )
                user_a = User(
                    id=uuid.uuid4(), tenant_id=tenant_a.id, email=f"ack-a-{suffix}@example.test",
                    password_hash="test-only-not-used", full_name="Tenant A agent", is_active=True,
                    is_superuser=False, is_platform_admin=False, auth_token_version=0,
                )
                user_a2 = User(
                    id=uuid.uuid4(), tenant_id=tenant_a.id, email=f"ack-a2-{suffix}@example.test",
                    password_hash="test-only-not-used", full_name="Tenant A second agent", is_active=True,
                    is_superuser=False, is_platform_admin=False, auth_token_version=0,
                )
                user_b = User(
                    id=uuid.uuid4(), tenant_id=tenant_b.id, email=f"ack-b-{suffix}@example.test",
                    password_hash="test-only-not-used", full_name="Tenant B agent", is_active=True,
                    is_superuser=False, is_platform_admin=False, auth_token_version=0,
                )
                session.add_all([employee, user_a, user_a2, user_b])
                await session.flush()

                channel = CustomerChannel(
                    id=uuid.uuid4(), tenant_id=tenant_a.id, employee_id=employee.id,
                    name="Handoff acknowledgement test", channel_type="web_widget",
                    public_key=f"pk_ack_{suffix}", config={}, is_active=True,
                )
                session.add(channel)
                await session.flush()

                conversation = CustomerConversation(
                    id=uuid.uuid4(), tenant_id=tenant_a.id, employee_id=employee.id,
                    channel_id=channel.id, customer_token_hash="a" * 64,
                    status="human", handoff_requested=True,
                )
                session.add(conversation)
                await session.flush()

                with pytest.raises(NotFoundError, match="Conversation not found"):
                    await acknowledge_handoff(
                        session, tenant_id=tenant_b.id,
                        conversation_id=conversation.id, user_id=user_b.id,
                    )

                claimed = await acknowledge_handoff(
                    session, tenant_id=tenant_a.id,
                    conversation_id=conversation.id, user_id=user_a.id,
                )
                assert claimed.assigned_user_id == user_a.id
                assert claimed.acknowledged_by_user_id == user_a.id
                assert claimed.acknowledged_at is not None

                # A second acknowledgement is idempotent and preserves the first timestamp.
                first_ack = claimed.acknowledged_at
                claimed_again = await acknowledge_handoff(
                    session, tenant_id=tenant_a.id,
                    conversation_id=conversation.id, user_id=user_a.id,
                )
                assert claimed_again.acknowledged_at == first_ack

                with pytest.raises(ConflictError, match="assigned to another user"):
                    await acknowledge_handoff(
                        session, tenant_id=tenant_a.id,
                        conversation_id=conversation.id, user_id=user_a2.id,
                    )

                reassigned = await update_handoff(
                    session, tenant_id=tenant_a.id, conversation_id=conversation.id,
                    requested=True, assigned_user_id=user_a2.id,
                )
                assert reassigned.assigned_user_id == user_a2.id
                assert reassigned.acknowledged_at is None
                assert reassigned.acknowledged_by_user_id is None

                reopened = await update_handoff(
                    session, tenant_id=tenant_a.id, conversation_id=conversation.id,
                    requested=False, assigned_user_id=None,
                )
                assert reopened.status == "open"
                assert reopened.handoff_requested is False
                assert reopened.acknowledged_at is None
    finally:
        await engine.dispose()
