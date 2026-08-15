class LegacyOrderCalculator:
    def __init__(self, legacy_service):
        self.legacy_service = legacy_service
    async def calculate(self, items):
        result = await self.legacy_service.calculate_total(items)
        return float(result)

class InMemoryOrderRepository:
    def __init__(self):
        self.items = {}
    async def save(self, order):
        self.items[str(order.id)] = order
        return order
    async def get(self, order_id):
        return self.items.get(order_id)
