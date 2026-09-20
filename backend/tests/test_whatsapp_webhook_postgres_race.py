"""Real PostgreSQL concurrency coverage for WhatsApp webhook admission."""

import asyncio
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, select

from app.api.v1.channel_webhooks import _enqueue_whatsapp_message
from app.core.database import AsyncSessionLocal
from app.models.conversation import CustomerConversation, CustomerMessage
from app.models.customer import Customer
from app.models.customer_channel import CustomerChannel
from app.models.employee import Employee
from app.models.tenant import Tenant


@pytest_asyncio.fixture
async def whatsapp_race_setup():
    async with AsyncSessionLocal() as db:
        tenant = Tenant(
            name="WhatsApp Race Test",
            slug=f"wa-race-{uuid.uuid4().hex[:12]}",
            status="active",
        )
        db.add(tenant)
        await db.flush()

        employee = Employee(
            tenant_id=tenant.id,
            slug=f"wa-race-employee-{uuid.uuid4().hex[:8]}",
            name="WhatsApp Race Test Employee",
            kind="custom",
            is_active=True,
        )
        db.add(employee)
        await db.flush()

        channel = CustomerChannel(
            tenant_id=tenant.id,
            employee_id=employee.id,
            name="WhatsApp Race Test Channel",
            channel_type="whatsapp",
            public_key=f"pk_wa_race_{uuid.uuid4().hex}",
            config={},
            is_active=True,
        )
        db.add(channel)
        await db.commit()

        yield SimpleNamespace(
            tenant_id=tenant.id,
            employee_id=employee.id,
            channel_id=channel.id,
            from_phone=f"+9891{uuid.uuid4().int % 10_000_000:07d}",
        )

        # Test runs create no persisted Run because run_service.create_run is
        # replaced with a deterministic in-test stub. Clean the durable rows.
        await db.execute(
            delete(CustomerMessage).where(CustomerMessage.tenant_id == tenant.id)
        )
        await db.execute(
            delete(CustomerConversation).where(CustomerConversation.tenant_id == tenant.id)
        )
        await db.execute(
            delete(Customer).where(Customer.tenant_id == tenant.id)
        )
        await db.execute(delete(CustomerChannel).where(CustomerChannel.id == channel.id))
        await db.execute(delete(Employee).where(Employee.id == employee.id))
        await db.execute(delete(Tenant).where(Tenant.id == tenant.id))
        await db.commit()


@pytest.mark.asyncio
async def test_concurrent_same_provider_message_creates_one_message_and_one_run(
    whatsapp_race_setup, monkeypatch
):
    data = whatsapp_race_setup
    run_ids = [uuid.uuid4() for _ in range(2)]

    async def create_run(*args, **kwargs):
        return SimpleNamespace(id=run_ids.pop(0), conversation_id=None)

    async def enqueue(*args, **kwargs):
        return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr("app.services.run_service.create_run", create_run)
    monkeypatch.setattr("app.api.v1.channel_webhooks.outbox_service.enqueue", enqueue)

    async def submit(run_number: int):
        async with AsyncSessionLocal() as db:
            channel = (
                await db.execute(
                    select(CustomerChannel).where(CustomerChannel.id == data.channel_id)
                )
            ).scalar_one()
            return await _enqueue_whatsapp_message(
                db,
                channel,
                from_phone=data.from_phone,
                text="same provider message",
                provider_message_id="wamid-race-1",
            )

    first, second = await asyncio.gather(submit(1), submit(2))

    async with AsyncSessionLocal() as db:
        conversations = list(
            (
                await db.execute(
                    select(CustomerConversation).where(
                        CustomerConversation.channel_id == data.channel_id
                    )
                )
            )
            .scalars()
            .all()
        )
        messages = list(
            (
                await db.execute(
                    select(CustomerMessage).where(
                        CustomerMessage.channel_id == data.channel_id,
                        CustomerMessage.provider_message_id == "wamid-race-1",
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(conversations) == 1
    assert len(messages) == 1
    assert first[0].id == second[0].id
    assert sorted([first[1], second[1]]) == sorted(
        [messages[0].run_id, messages[0].run_id]
    )
    assert sorted([first[2], second[2]]) == [False, True]


@pytest.mark.asyncio
async def test_concurrent_same_sender_different_provider_ids_reuses_one_conversation(
    whatsapp_race_setup, monkeypatch
):
    data = whatsapp_race_setup
    run_ids = [uuid.uuid4() for _ in range(2)]

    async def create_run(*args, **kwargs):
        return SimpleNamespace(id=run_ids.pop(0), conversation_id=None)

    async def enqueue(*args, **kwargs):
        return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr("app.services.run_service.create_run", create_run)
    monkeypatch.setattr("app.api.v1.channel_webhooks.outbox_service.enqueue", enqueue)

    async def submit(provider_id: str):
        async with AsyncSessionLocal() as db:
            channel = (
                await db.execute(
                    select(CustomerChannel).where(CustomerChannel.id == data.channel_id)
                )
            ).scalar_one()
            return await _enqueue_whatsapp_message(
                db,
                channel,
                from_phone=data.from_phone,
                text=provider_id,
                provider_message_id=provider_id,
            )

    first, second = await asyncio.gather(
        submit("wamid-race-a"),
        submit("wamid-race-b"),
    )

    async with AsyncSessionLocal() as db:
        conversations = list(
            (
                await db.execute(
                    select(CustomerConversation).where(
                        CustomerConversation.channel_id == data.channel_id
                    )
                )
            )
            .scalars()
            .all()
        )
        messages = list(
            (
                await db.execute(
                    select(CustomerMessage).where(
                        CustomerMessage.channel_id == data.channel_id
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(conversations) == 1
    assert len(messages) == 2
    assert {message.provider_message_id for message in messages} == {
        "wamid-race-a",
        "wamid-race-b",
    }
    assert first[0].id == second[0].id
    assert first[2] is False
    assert second[2] is False
