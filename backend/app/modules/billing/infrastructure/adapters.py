class LegacyPaymentGateway:
    def __init__(self, legacy_service):
        self.legacy_service = legacy_service
    async def charge(self, customer_id, amount):
        return await self.legacy_service.charge(customer_id, amount)

class InMemoryInvoiceRepository:
    def __init__(self): self.items={}
    async def save(self, invoice):
        self.items[str(invoice.id)] = invoice
        return invoice
    async def get(self, invoice_id): return self.items.get(invoice_id)
