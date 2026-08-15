from __future__ import annotations
import uuid
from app.shared.events import DomainEvent
from app.shared.event_catalog import ORDER_COMPLETED
from app.modules.commerce.domain.models import Order

class CommerceApplicationService:
    def __init__(self, repository, calculator, event_bus):
        self.repository = repository
        self.calculator = calculator
        self.event_bus = event_bus

    async def create_order(self, *, customer_id, items, tenant_id=None):
        total = await self.calculator.calculate(items)
        order = Order(uuid.uuid4(), tenant_id, customer_id, "completed", items, total)
        await self.repository.save(order)
        await self.event_bus.publish(DomainEvent(
            name=ORDER_COMPLETED,
            tenant_id=tenant_id,
            payload={"order_id": str(order.id), "customer_id": str(customer_id), "total": total},
        ))
        return order
