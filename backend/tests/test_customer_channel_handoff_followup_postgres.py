"""PostgreSQL regression: messages after human handoff must not create AI Runs.

Only the dedicated local support_test database is accepted. The test skips when
SUPPORT_TEST_DATABASE_URL is absent and fails closed for any other target.
"""

import os
import uuid

import pytest
from sqlalchemy import func, select
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
            "Refusing to run handoff-message integration test outside the "
            "dedicated local support_test database."
        )
    return url


@pytest.mark.asyncio
async def test_followup_customer_message_after_handoff_is_saved_without_ai_run(monkeypatch):
    from app.models.conversation import CustomerConversation, CustomerMessage
    from app.models.customer_channel import CustomerChannel
    from app.models.employee import Employee
    from app.models.run import Run
    from app.models.tenant import Tenant
    from app.services import customer_channel_service
    from app.services.customer_channel_service import _hash_token, send_message

    engine = create_async_engine(_support_test_database_url(), poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex
    token = f"handoff-followup-token-{suffix}"

    async def forbidden_create_run(*args, **kwargs):
        raise AssertionError("AI Run creation must not occur after human handoff")

    monkeypatch.setattr(customer_channel_service.run_service, "create_run", forbidden_create_run)

    try:
        async with sessions() as session:
            async with session.begin():
                tenant = Tenant(
                    id=uuid.uuid4(),
                    name=f"Handoff follow-up tenant {suffix}",
                    slug=f"handoff-followup-{suffix}",
                    tenant_kind="customer",
                    status="active",
                )
                session.add(tenant)
                await session.flush()

                employee = Employee(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    slug=f"handoff-followup-agent-{suffix}",
                    name="Handoff follow-up test agent",
                    kind="custom",
                    is_active=True,
                )
                session.add(employee)
                await session.flush()

                channel = CustomerChannel(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    employee_id=employee.id,
                    name="PostgreSQL handoff follow-up test",
                    channel_type="web_widget",
                    public_key=f"pk_handoff_followup_{suffix}",
                    config={},
                    is_active=True,
                )
                session.add(channel)
                await session.flush()

                conversation = CustomerConversation(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    employee_id=employee.id,
                    channel_id=channel.id,
                    customer_token_hash=_hash_token(token),
                    customer_name="Synthetic customer",
                    status="human",
                    handoff_requested=True,
                )
                session.add(conversation)
                await session.flush()

                prior_message = CustomerMessage(
                    tenant_id=tenant.id,
                    conversation_id=conversation.id,
                    channel_id=channel.id,
                    role="user",
                    content="Please connect me to a human",
                )
                session.add(prior_message)
                await session.flush()

                followup_text = "I can provide the order number now."
                returned_conversation, run = await send_message(
                    session,
                    conversation_id=conversation.id,
                    token=token,
                    content=followup_text,
                )

                assert returned_conversation.id == conversation.id
                assert returned_conversation.status == "human"
                assert returned_conversation.handoff_requested is True
                assert run is None

                messages = list(
                    (
                        await session.execute(
                            select(CustomerMessage)
                            .where(
                                CustomerMessage.conversation_id == conversation.id,
                                CustomerMessage.tenant_id == tenant.id,
                            )
                            .order_by(CustomerMessage.created_at.asc())
                        )
                    ).scalars().all()
                )
                assert any(
                    message.role == "user" and message.content == followup_text
                    for message in messages
                )
                run_count = (
                    await session.execute(
                        select(func.count(Run.id)).where(
                            Run.conversation_id == conversation.id,
                            Run.tenant_id == tenant.id,
                        )
                    )
                ).scalar_one()
                assert run_count == 0
    finally:
        await engine.dispose()
