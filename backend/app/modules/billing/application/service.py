from __future__ import annotations
import uuid
from app.shared.events import DomainEvent
from app.shared.event_catalog import INVOICE_ISSUED, PAYMENT_SUCCEEDED
from app.modules.billing.domain.models import Invoice

class BillingApplicationService:
    def __init__(self, repository, gateway, event_bus):
        self.repository, self.gateway, self.event_bus = repository, gateway, event_bus

    async def issue_and_pay(self, *, customer_id, amount, tenant_id=None):
        invoice = Invoice(uuid.uuid4(), tenant_id, customer_id, float(amount), "issued")
        await self.repository.save(invoice)
        await self.event_bus.publish(DomainEvent(
            name=INVOICE_ISSUED, tenant_id=tenant_id,
            payload={"invoice_id": str(invoice.id), "amount": invoice.amount},
        ))
        await self.gateway.charge(str(customer_id), invoice.amount)
        paid = Invoice(invoice.id, tenant_id, customer_id, invoice.amount, "paid")
        await self.repository.save(paid)
        await self.event_bus.publish(DomainEvent(
            name=PAYMENT_SUCCEEDED, tenant_id=tenant_id,
            payload={"invoice_id": str(invoice.id), "amount": invoice.amount},
        ))
        return paid
