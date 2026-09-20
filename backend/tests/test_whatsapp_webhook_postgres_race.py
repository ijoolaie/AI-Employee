"""Real PostgreSQL concurrency coverage for WhatsApp webhook admission."""

import asyncio
import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.api.v1.channel_webhooks import _enqueue_whatsapp_message
from app.core.database import AsyncSessionLocal
from app.models.conversation import CustomerConversation, CustomerMessage
from app.models.customer import Customer
from app.models.customer_channel import CustomerChannel
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
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

        version = EmployeeVersion(
            employee_id=employee.id,
            version_number=1,
            is_current=True,
            input_schema={},
            output_schema={},
            prompt_template="",
            allowed_tools=[],
            rules={},
        )
        db.add(version)
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
            employee_version_id=version.id,
            channel_id=channel.id,
            from_phone=f"+9891{uuid.uuid4().int % 10_000_000:07d}",
        )

        await db.execute(
            delete(CustomerMessage).where(CustomerMessage.tenant_id == tenant.id)
        )
        await db.execute(
            delete(CustomerConversation).where(CustomerConversation.tenant_id == tenant.id)
        )
        await db.execute(delete(Customer).where(Customer.tenant_id == tenant.id))
        await db.execute(delete(Run).where(Run.tenant_id == tenant.id))
        await db.execute(delete(CustomerChannel).where(CustomerChannel.id == channel.id))
        await db.execute(
            delete(EmployeeVersion).where(EmployeeVersion.employee_id == employee.id)
        )
        await db.execute(delete(Employee).where(Employee.id == employee.id))
        await db.execute(delete(Tenant).where(Tenant.id == tenant.id))
        await db.commit()


@pytest.mark.asyncio
async def test_concurrent_same_provider_message_creates_one_message_and_one_run(
    whatsapp_race_setup, monkeypatch
):
    data = whatsapp_race_setup
    run_ids = [uuid.uuid4() for _ in range(2)]

    async def create_run(
        db, *, tenant_id, employee_id, input_data, created_by,
        employee_version_id=None, agent_instance_id=None
    ):
        version = (
            await db.execute(
                select(EmployeeVersion).where(
                    EmployeeVersion.employee_id == employee_id,
                    EmployeeVersion.id == (employee_version_id or data.employee_version_id),
                )
            )
        ).scalar_one()
        run = Run(
            id=run_ids.pop(0),
            tenant_id=tenant_id,
            employee_id=employee_id,
            employee_version_id=version.id,
            agent_instance_id=agent_instance_id,
            created_by=created_by,
            status="pending",
            input_data=input_data,
        )
        db.add(run)
        await db.flush()
        return run

    async def enqueue(*args, **kwargs):
        return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr("app.services.run_service.create_run", create_run)
    monkeypatch.setattr("app.api.v1.channel_webhooks.outbox_service.enqueue", enqueue)

    async def submit():
        async with AsyncSessionLocal() as db:
            channel = (
                await db.execute(
                    select(CustomerChannel).where(CustomerChannel.id == data.channel_id)
                )
            ).scalar_one()
            result = await _enqueue_whatsapp_message(
                db,
                channel,
                from_phone=data.from_phone,
                text="same provider message",
                provider_message_id="wamid-race-1",
            )
            await db.commit()
            return result

    first, second = await asyncio.gather(submit(), submit())

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
    assert first[1] == second[1] == messages[0].run_id
    assert sorted([first[2], second[2]]) == [False, True]


@pytest.mark.asyncio
async def test_concurrent_same_sender_different_provider_ids_reuses_one_conversation(
    whatsapp_race_setup, monkeypatch
):
    data = whatsapp_race_setup
    run_ids = [uuid.uuid4() for _ in range(2)]

    async def create_run(
        db, *, tenant_id, employee_id, input_data, created_by,
        employee_version_id=None, agent_instance_id=None
    ):
        run = Run(
            id=run_ids.pop(0),
            tenant_id=tenant_id,
            employee_id=employee_id,
            employee_version_id=employee_version_id or data.employee_version_id,
            agent_instance_id=agent_instance_id,
            created_by=created_by,
            status="pending",
            input_data=input_data,
        )
        db.add(run)
        await db.flush()
        return run

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
            result = await _enqueue_whatsapp_message(
                db,
                channel,
                from_phone=data.from_phone,
                text=provider_id,
                provider_message_id=provider_id,
            )
            await db.commit()
            return result

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
    assert first[1] != second[1]
    assert first[2] is False
    assert second[2] is False


@pytest.mark.asyncio
async def test_public_chat_allows_multiple_conversations_for_same_customer(
    whatsapp_race_setup,
):
    """Public Chat must not inherit WhatsApp's one-conversation-per-sender key."""
    data = whatsapp_race_setup

    from app.services.customer_channel_service import create_conversation

    async with AsyncSessionLocal() as db:
        channel = (
            await db.execute(
                select(CustomerChannel).where(CustomerChannel.id == data.channel_id)
            )
        ).scalar_one()

        first, first_token, _ = await create_conversation(
            db,
            public_key=channel.public_key,
            customer_name="Public Chat Customer",
            customer_email="same-customer@example.com",
            customer_phone=None,
        )
        await db.commit()

        second, second_token, _ = await create_conversation(
            db,
            public_key=channel.public_key,
            customer_name="Public Chat Customer",
            customer_email="same-customer@example.com",
            customer_phone=None,
        )
        await db.commit()

        customers = list(
            (
                await db.execute(
                    select(Customer).where(
                        Customer.tenant_id == data.tenant_id,
                        Customer.external_key == "same-customer@example.com",
                    )
                )
            )
            .scalars()
            .all()
        )
        conversations = list(
            (
                await db.execute(
                    select(CustomerConversation).where(
                        CustomerConversation.tenant_id == data.tenant_id,
                        CustomerConversation.customer_id == customers[0].id,
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(customers) == 1
    assert len(conversations) == 2
    assert first.id != second.id
    assert first_token != second_token
    assert {conversation.id for conversation in conversations} == {first.id, second.id}


@pytest.mark.asyncio
async def test_public_chat_concurrent_starts_create_independent_conversations(
    whatsapp_race_setup,
):
    """Concurrent Public Chat starts for one customer remain separate sessions."""
    data = whatsapp_race_setup

    from app.services.customer_channel_service import create_conversation

    async def create_one():
        async with AsyncSessionLocal() as db:
            channel = (
                await db.execute(
                    select(CustomerChannel).where(CustomerChannel.id == data.channel_id)
                )
            ).scalar_one()
            conversation, token, _ = await create_conversation(
                db,
                public_key=channel.public_key,
                customer_name="Concurrent Public Customer",
                customer_email="concurrent@example.com",
                customer_phone=None,
            )
            await db.commit()
            return conversation.id, token

    first, second = await asyncio.gather(create_one(), create_one())

    async with AsyncSessionLocal() as db:
        customer = (
            await db.execute(
                select(Customer).where(
                    Customer.tenant_id == data.tenant_id,
                    Customer.external_key == "concurrent@example.com",
                )
            )
        ).scalar_one()
        conversations = list(
            (
                await db.execute(
                    select(CustomerConversation).where(
                        CustomerConversation.tenant_id == data.tenant_id,
                        CustomerConversation.customer_id == customer.id,
                    )
                )
            )
            .scalars()
            .all()
        )

    assert first[0] != second[0]
    assert first[1] != second[1]
    assert len(conversations) == 2


@pytest.mark.asyncio
async def test_meta_webhook_http_replay_is_idempotent(whatsapp_race_setup, monkeypatch):
    """The Meta webhook handler admits one provider message across a replay."""
    data = whatsapp_race_setup
    from app.api.v1.channel_webhooks import whatsapp_meta_inbound
    from starlette.requests import Request

    run_id = uuid.uuid4()

    async def create_run(
        db, *, tenant_id, employee_id, input_data, created_by,
        employee_version_id=None, agent_instance_id=None
    ):
        run = Run(
            id=run_id,
            tenant_id=tenant_id,
            employee_id=employee_id,
            employee_version_id=employee_version_id or data.employee_version_id,
            created_by=created_by,
            status="pending",
            input_data=input_data,
        )
        db.add(run)
        await db.flush()
        return run

    async def enqueue(*args, **kwargs):
        return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr("app.services.run_service.create_run", create_run)
    monkeypatch.setattr("app.api.v1.channel_webhooks.outbox_service.enqueue", enqueue)

    secret = "meta-replay-test-secret"
    async with AsyncSessionLocal() as db:
        channel = (
            await db.execute(
                select(CustomerChannel).where(CustomerChannel.id == data.channel_id)
            )
        ).scalar_one()
        channel.config = {"meta_app_secret": secret}
        await db.commit()

    import hashlib
    import hmac
    import json

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "wamid-http-replay-1",
                                    "from": data.from_phone,
                                    "type": "text",
                                    "text": {"body": "hello from Meta"},
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }
    raw_body = json.dumps(payload, separators=(",", ":")).encode()
    signature = "sha256=" + hmac.new(
        secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()

    def request_for_body() -> Request:
        delivered = False

        async def receive():
            nonlocal delivered
            if delivered:
                return {"type": "http.request", "body": b"", "more_body": False}
            delivered = True
            return {"type": "http.request", "body": raw_body, "more_body": False}

        return Request(
            {
                "type": "http",
                "method": "POST",
                "path": f"/api/v1/webhooks/channels/whatsapp/meta/{data.channel_id}",
                "headers": [
                    (b"host", b"testserver"),
                    (b"x-hub-signature-256", signature.encode()),
                    (b"content-type", b"application/json"),
                ],
            },
            receive=receive,
        )

    async with AsyncSessionLocal() as db:
        first = await whatsapp_meta_inbound(
            data.channel_id,
            request_for_body(),
            db,
            signature,
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        second = await whatsapp_meta_inbound(
            data.channel_id,
            request_for_body(),
            db,
            signature,
        )
        await db.commit()

    assert first == {"success": True, "processed": 1, "duplicates": 0}
    assert second == {"success": True, "processed": 0, "duplicates": 1}

    async with AsyncSessionLocal() as db:
        messages = list(
            (
                await db.execute(
                    select(CustomerMessage).where(
                        CustomerMessage.channel_id == data.channel_id,
                        CustomerMessage.provider_message_id == "wamid-http-replay-1",
                    )
                )
            )
            .scalars()
            .all()
        )
        runs = list(
            (
                await db.execute(
                    select(Run).where(
                        Run.tenant_id == data.tenant_id,
                        Run.id == run_id,
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(messages) == 1
    assert len(runs) == 1
    assert messages[0].run_id == run_id
