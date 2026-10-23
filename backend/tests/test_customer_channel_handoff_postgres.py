"""PostgreSQL-backed tenant-isolation regression for customer handoff.

This test only runs against the dedicated local support_test database. It skips
when that explicit test database URL is not configured and fails closed if the
URL points anywhere else.
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
        raise RuntimeError(
            "Refusing to run customer handoff integration test outside the "
            "dedicated local support_test database."
        )
    return url


@pytest.mark.asyncio
async def test_handoff_is_persisted_and_assignee_is_tenant_scoped_in_postgres():
    from sqlalchemy import select

    from app.core.exceptions import NotFoundError
    from app.models.customer_channel import CustomerChannel
    from app.models.conversation import CustomerConversation
    from app.models.employee import Employee
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.services.customer_channel_service import update_handoff

    engine = create_async_engine(_support_test_database_url(), poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex

    try:
        # A transaction is deliberately rolled back at the end; the test leaves
        # no fixture records in the shared, isolated CI regression database.
        async with sessions() as session:
            async with session.begin():
                tenant_a = Tenant(
                    id=uuid.uuid4(), name=f"Handoff tenant A {suffix}",
                    slug=f"handoff-a-{suffix}", tenant_kind="customer", status="active",
                )
                tenant_b = Tenant(
                    id=uuid.uuid4(), name=f"Handoff tenant B {suffix}",
                    slug=f"handoff-b-{suffix}", tenant_kind="customer", status="active",
                )
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
                channel = CustomerChannel(
                    id=uuid.uuid4(), tenant_id=tenant_a.id, employee_id=employee.id,
                    name="PostgreSQL handoff test", channel_type="web_widget",
                    public_key=f"pk_handoff_{suffix}", config={}, is_active=True,
                )
                conversation = CustomerConversation(
                    id=uuid.uuid4(), tenant_id=tenant_a.id,
                    employee_id=employee.id, channel_id=channel.id,
                    customer_token_hash=("0" * 64), customer_name="Synthetic customer",
                    status="open", handoff_requested=False,
                )
                session.add_all([
                    tenant_a, tenant_b, employee, same_tenant_user,
                    foreign_tenant_user, channel, conversation,
                ])
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

                # Confirm the flushed row can be queried back from PostgreSQL.
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
    finally:
        await engine.dispose()
