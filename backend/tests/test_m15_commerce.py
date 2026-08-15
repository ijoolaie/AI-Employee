import uuid
import pytest
from app.modules.commerce.application.service import CommerceApplicationService
from app.modules.commerce.infrastructure.adapters import InMemoryOrderRepository

class Calc:
    async def calculate(self, items):
        return sum(x["price"] * x["qty"] for x in items)
class Bus:
    def __init__(self): self.events=[]
    async def publish(self,e): self.events.append(e)

@pytest.mark.asyncio
async def test_create_order():
    repo, bus = InMemoryOrderRepository(), Bus()
    svc = CommerceApplicationService(repo, Calc(), bus)
    customer = uuid.uuid4()
    order = await svc.create_order(customer_id=customer, items=[{"price":10,"qty":2}])
    assert order.status == "completed"
    assert order.total == 20
    assert bus.events[0].name == "commerce.order.completed"
