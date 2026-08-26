import uuid

import pytest
from sqlalchemy import select

from app.models.conversation import CustomerConversation, CustomerMessage


@pytest.mark.asyncio
async def test_conversation_message_query_must_be_tenant_scoped(db_session):
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    conversation_id = uuid.uuid4()

    conversation = CustomerConversation(
        id=conversation_id,
        tenant_id=tenant_a,
        employee_id=uuid.uuid4(),
        channel_id=uuid.uuid4(),
        customer_token_hash="a" * 64,
    )
    db_session.add(conversation)
    db_session.add(
        CustomerMessage(
            tenant_id=tenant_a,
            conversation_id=conversation_id,
            role="user",
            content="tenant-a message",
        )
    )
    await db_session.flush()

    rows = (
        await db_session.execute(
            select(CustomerMessage).where(
                CustomerMessage.conversation_id == conversation_id,
                CustomerMessage.tenant_id == tenant_b,
            )
        )
    ).scalars().all()

    assert rows == []


@pytest.mark.asyncio
async def test_conversation_message_query_returns_owner_tenant_only(db_session):
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    conversation_id = uuid.uuid4()

    db_session.add(
        CustomerConversation(
            id=conversation_id,
            tenant_id=tenant_a,
            employee_id=uuid.uuid4(),
            channel_id=uuid.uuid4(),
            customer_token_hash="b" * 64,
        )
    )
    db_session.add_all(
        [
            CustomerMessage(
                tenant_id=tenant_a,
                conversation_id=conversation_id,
                role="user",
                content="owner",
            ),
            CustomerMessage(
                tenant_id=tenant_b,
                conversation_id=conversation_id,
                role="user",
                content="foreign",
            ),
        ]
    )
    await db_session.flush()

    rows = (
        await db_session.execute(
            select(CustomerMessage).where(
                CustomerMessage.conversation_id == conversation_id,
                CustomerMessage.tenant_id == tenant_a,
            )
        )
    ).scalars().all()

    assert [row.content for row in rows] == ["owner"]
