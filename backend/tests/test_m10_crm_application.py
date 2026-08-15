import uuid
import pytest

from app.modules.crm.application.service import CRMApplicationService
from app.modules.crm.infrastructure.in_memory import (
    InMemoryCustomerRepository,
    InMemoryConversationRepository,
    InMemoryIdentityResolver,
)

class FakeBus:
    def __init__(self):
        self.events = []
    async def publish(self, event):
        self.events.append(event)

@pytest.mark.asyncio
async def test_crm_creates_customer_and_publishes_event():
    customers = InMemoryCustomerRepository()
    conversations = InMemoryConversationRepository()
    resolver = InMemoryIdentityResolver()
    bus = FakeBus()

    service = CRMApplicationService(customers, conversations, resolver, bus)
    customer = await service.create_or_resolve_customer(
        name="Test Customer",
        email="test@example.com",
        tenant_id=uuid.uuid4(),
    )

    assert customer.status == "active"
    assert await customers.get(str(customer.id)) == customer
    assert len(bus.events) == 1
    assert bus.events[0].name == "crm.customer.created"

@pytest.mark.asyncio
async def test_crm_reuses_existing_customer():
    customers = InMemoryCustomerRepository()
    conversations = InMemoryConversationRepository()
    resolver = InMemoryIdentityResolver()
    bus = FakeBus()
    service = CRMApplicationService(customers, conversations, resolver, bus)

    first = await service.create_or_resolve_customer(
        name="Existing",
        email="same@example.com",
    )
    resolver.by_email["same@example.com"] = str(first.id)

    second = await service.create_or_resolve_customer(
        name="Should Not Duplicate",
        email="same@example.com",
    )

    assert second.id == first.id
    assert len(customers.items) == 1
    assert len(bus.events) == 1

@pytest.mark.asyncio
async def test_crm_opens_conversation():
    customers = InMemoryCustomerRepository()
    conversations = InMemoryConversationRepository()
    resolver = InMemoryIdentityResolver()
    bus = FakeBus()
    service = CRMApplicationService(customers, conversations, resolver, bus)

    customer = await service.create_or_resolve_customer(name="Customer")
    conversation = await service.open_conversation(
        customer_id=customer.id,
        channel="web",
    )

    assert conversation.customer_id == customer.id
    assert conversation.status == "open"
    assert await conversations.get(str(conversation.id)) == conversation
