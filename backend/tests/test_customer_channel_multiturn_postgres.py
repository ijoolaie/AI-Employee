"""PostgreSQL-backed regression for authorized multi-turn customer transcript loading.

The test only uses the dedicated local support_test database. It skips when the
explicit test URL is absent and fails closed when the URL points elsewhere.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
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
            "Refusing to run customer transcript integration test outside the "
            "dedicated local support_test database."
        )
    return url


@pytest.mark.asyncio
async def test_postgres_transcript_is_chronological_and_tenant_scoped():
    from app.models.conversation import CustomerConversation, CustomerMessage
    from app.models.customer_channel import CustomerChannel
    from app.models.employee import Employee
    from app.models.tenant import Tenant
    from app.services.customer_channel_service import (
        _format_conversation_transcript,
        _hash_token,
    )

    engine = create_async_engine(_support_test_database_url(), poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex
    try:
        async with sessions() as session:
            async with session.begin():
                tenant_a = Tenant(
                    id=uuid.uuid4(), name=f"Transcript tenant A {suffix}",
                    slug=f"transcript-a-{suffix}", tenant_kind="customer", status="active",
                )
                tenant_b = Tenant(
                    id=uuid.uuid4(), name=f"Transcript tenant B {suffix}",
                    slug=f"transcript-b-{suffix}", tenant_kind="customer", status="active",
                )
                session.add_all([tenant_a, tenant_b])
                await session.flush()

                employee = Employee(
                    id=uuid.uuid4(), tenant_id=tenant_a.id,
                    slug=f"transcript-agent-{suffix}", name="Transcript test agent",
                    kind="custom", is_active=True,
                )
                session.add(employee)
                await session.flush()

                channel = CustomerChannel(
                    id=uuid.uuid4(), tenant_id=tenant_a.id, employee_id=employee.id,
                    name="PostgreSQL transcript test", channel_type="web_widget",
                    public_key=f"pk_transcript_{suffix}", config={}, is_active=True,
                )
                session.add(channel)
                await session.flush()

                conversation = CustomerConversation(
                    id=uuid.uuid4(), tenant_id=tenant_a.id,
                    employee_id=employee.id, channel_id=channel.id,
                    customer_token_hash=_hash_token(f"transcript-token-{suffix}"),
                    customer_name="Synthetic customer", status="open",
                    handoff_requested=False,
                )
                session.add(conversation)
                await session.flush()

                start = datetime(2026, 1, 1, tzinfo=timezone.utc)
                expected = [
                    ("user", "هزینه ارسال چقدره؟"),
                    ("assistant", "ارسال برای کدوم شهره؟"),
                    ("user", "تهران"),
                ]
                for index, (role, message_text) in enumerate(expected):
                    session.add(CustomerMessage(
                        id=uuid.uuid4(), tenant_id=tenant_a.id,
                        conversation_id=conversation.id, channel_id=channel.id,
                        role=role, content=message_text,
                        created_at=start + timedelta(seconds=index),
                    ))
                # A row with another tenant must never enter the authorized transcript.
                session.add(CustomerMessage(
                    id=uuid.uuid4(), tenant_id=tenant_b.id,
                    conversation_id=conversation.id, channel_id=None,
                    role="assistant", content="FOREIGN TENANT DATA",
                    created_at=start + timedelta(seconds=4),
                ))
                await session.flush()

                rows = list((await session.execute(
                    select(CustomerMessage)
                    .where(
                        CustomerMessage.conversation_id == conversation.id,
                        CustomerMessage.tenant_id == tenant_a.id,
                    )
                    .order_by(CustomerMessage.created_at.desc())
                    .limit(30)
                )).scalars().all())
                rows.reverse()
                transcript = _format_conversation_transcript(rows)

                assert transcript.splitlines() == [
                    "Customer: هزینه ارسال چقدره؟",
                    "Assistant: ارسال برای کدوم شهره؟",
                    "Customer: تهران",
                ]
                assert "FOREIGN TENANT DATA" not in transcript
                assert len(rows) == 3
    finally:
        await engine.dispose()
