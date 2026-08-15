from __future__ import annotations
from typing import Any
import uuid

from app.shared.events import DomainEvent
from app.shared.event_catalog import CUSTOMER_CREATED
from app.modules.crm.domain.models import Customer, Conversation
from app.modules.crm.domain.ports import (
    CustomerRepository,
    ConversationRepository,
    CustomerIdentityResolver,
)

class CRMApplicationService:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        conversation_repository: ConversationRepository,
        identity_resolver: CustomerIdentityResolver,
        event_bus,
    ) -> None:
        self.customer_repository = customer_repository
        self.conversation_repository = conversation_repository
        self.identity_resolver = identity_resolver
        self.event_bus = event_bus

    async def create_or_resolve_customer(
        self,
        *,
        name: str,
        email: str | None = None,
        external_id: str | None = None,
        tenant_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Customer:
        existing = await self.identity_resolver.resolve(email, external_id)
        if existing and existing.get("customer_id"):
            customer = await self.customer_repository.get(str(existing["customer_id"]))
            if customer:
                return customer

        customer = Customer(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=name,
            email=email,
            status="active",
            metadata=metadata or {},
        )
        await self.customer_repository.save(customer)

        await self.event_bus.publish(
            DomainEvent(
                name=CUSTOMER_CREATED,
                tenant_id=tenant_id,
                payload={"customer_id": str(customer.id), "email": email},
            )
        )
        return customer

    async def open_conversation(
        self,
        *,
        customer_id: uuid.UUID,
        channel: str,
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        conversation = Conversation(
            id=uuid.uuid4(),
            customer_id=customer_id,
            channel=channel,
            status="open",
            metadata=metadata or {},
        )
        return await self.conversation_repository.save(conversation)
