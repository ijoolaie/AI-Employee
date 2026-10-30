"""PostgreSQL integration coverage for tenant-safe support slot provenance."""

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
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
        raise RuntimeError("Refusing to run support slot integration test outside support_test")
    return url


@pytest.mark.asyncio
async def test_slots_are_tenant_scoped_expiring_and_source_message_bound():
    from app.models.conversation import CustomerConversation, CustomerMessage
    from app.models.customer_channel import CustomerChannel
    from app.models.customer_conversation_slot import CustomerConversationSlot
    from app.models.employee import Employee
    from app.models.tenant import Tenant
    from app.services.customer_support_slots import (
        extract_explicit_customer_slots,
        load_valid_customer_conversation_slots,
        upsert_customer_conversation_slots,
    )

    engine = create_async_engine(_support_test_database_url(), poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    tenant_a_id, tenant_b_id = uuid.uuid4(), uuid.uuid4()
    conversation_a_id, conversation_b_id = uuid.uuid4(), uuid.uuid4()
    message_a_id, message_b_id = uuid.uuid4(), uuid.uuid4()
    try:
        async with sessions() as session:
            async with session.begin():
                tenant_a = Tenant(
                    id=tenant_a_id, name=f"Slot tenant A {suffix}",
                    slug=f"slot-a-{suffix}", tenant_kind="customer", status="active",
                )
                tenant_b = Tenant(
                    id=tenant_b_id, name=f"Slot tenant B {suffix}",
                    slug=f"slot-b-{suffix}", tenant_kind="customer", status="active",
                )
                session.add_all([tenant_a, tenant_b])
                await session.flush()

                employee_a = Employee(
                    id=uuid.uuid4(), tenant_id=tenant_a_id, slug=f"slot-a-agent-{suffix}",
                    name="Slot test A", kind="custom", is_active=True,
                )
                employee_b = Employee(
                    id=uuid.uuid4(), tenant_id=tenant_b_id, slug=f"slot-b-agent-{suffix}",
                    name="Slot test B", kind="custom", is_active=True,
                )
                session.add_all([employee_a, employee_b])
                await session.flush()

                channel_a = CustomerChannel(
                    id=uuid.uuid4(), tenant_id=tenant_a_id, employee_id=employee_a.id,
                    name="Slot channel A", channel_type="web_widget",
                    public_key=f"pk_slot_a_{suffix}", config={}, is_active=True,
                )
                channel_b = CustomerChannel(
                    id=uuid.uuid4(), tenant_id=tenant_b_id, employee_id=employee_b.id,
                    name="Slot channel B", channel_type="web_widget",
                    public_key=f"pk_slot_b_{suffix}", config={}, is_active=True,
                )
                session.add_all([channel_a, channel_b])
                await session.flush()

                conversation_a = CustomerConversation(
                    id=conversation_a_id, tenant_id=tenant_a_id, employee_id=employee_a.id,
                    channel_id=channel_a.id, customer_token_hash="a" * 64,
                    status="open", handoff_requested=False,
                )
                conversation_b = CustomerConversation(
                    id=conversation_b_id, tenant_id=tenant_b_id, employee_id=employee_b.id,
                    channel_id=channel_b.id, customer_token_hash="b" * 64,
                    status="open", handoff_requested=False,
                )
                session.add_all([conversation_a, conversation_b])
                await session.flush()

                session.add_all([
                    CustomerMessage(
                        id=message_a_id, tenant_id=tenant_a_id,
                        conversation_id=conversation_a_id, channel_id=channel_a.id,
                        role="user", content="تهران",
                    ),
                    CustomerMessage(
                        id=message_b_id, tenant_id=tenant_b_id,
                        conversation_id=conversation_b_id, channel_id=channel_b.id,
                        role="user", content="شیراز",
                    ),
                ])
                await session.flush()
                message_a_followup = CustomerMessage(
                    id=uuid.uuid4(), tenant_id=tenant_a_id,
                    conversation_id=conversation_a_id, channel_id=channel_a.id,
                    role="user", content="شماره سفارش: ORD-NEW\nتعداد: ۵",
                )
                session.add(message_a_followup)
                await session.flush()
                candidates = extract_explicit_customer_slots(message_a_followup.content)
                assert candidates == {"order_id": "ORD-NEW", "quantity": 5}
                await upsert_customer_conversation_slots(
                    session,
                    tenant_id=tenant_a_id,
                    conversation_id=conversation_a_id,
                    source_message_id=message_a_followup.id,
                    candidates=candidates,
                    now=now,
                )
                session.add_all([
                    CustomerConversationSlot(
                        tenant_id=tenant_a_id, conversation_id=conversation_a_id,
                        source_message_id=message_a_id, slot_name="city", value="تهران",
                        captured_at=now, expires_at=now + timedelta(days=30),
                    ),
                    CustomerConversationSlot(
                        tenant_id=tenant_b_id, conversation_id=conversation_b_id,
                        source_message_id=message_b_id, slot_name="reason", value="FOREIGN-SOURCE",
                        captured_at=now, expires_at=now + timedelta(days=30),
                    ),
                    CustomerConversationSlot(
                        tenant_id=tenant_a_id, conversation_id=conversation_a_id,
                        source_message_id=message_a_id, slot_name="payment_reference", value="PAY-OLD",
                        captured_at=now - timedelta(days=3), expires_at=now - timedelta(days=1),
                    ),
                ])
                await session.flush()

        async with sessions() as session:
            slots_a = await load_valid_customer_conversation_slots(
                session, tenant_id=tenant_a_id, conversation_id=conversation_a_id, now=now,
            )
            slots_b = await load_valid_customer_conversation_slots(
                session, tenant_id=tenant_b_id, conversation_id=conversation_b_id, now=now,
            )
            assert slots_a == {"city": "تهران", "order_id": "ORD-NEW", "quantity": 5}
            assert slots_b == {}, "A slot whose value is absent from its source customer message must be rejected"

        # A slot cannot pair tenant A's conversation with tenant B's source row.
        async with sessions() as session:
            session.add(CustomerConversationSlot(
                tenant_id=tenant_a_id, conversation_id=conversation_a_id,
                source_message_id=message_b_id, slot_name="reason", value="FOREIGN-SOURCE",
                captured_at=now, expires_at=now + timedelta(days=30),
            ))
            with pytest.raises(IntegrityError):
                await session.flush()
            await session.rollback()
    finally:
        await engine.dispose()
