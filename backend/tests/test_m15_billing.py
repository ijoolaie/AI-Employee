import uuid
import pytest
from app.modules.billing.application.service import BillingApplicationService
from app.modules.billing.infrastructure.adapters import InMemoryInvoiceRepository

class Gateway:
    def __init__(self): self.charges=[]
    async def charge(self,c,a): self.charges.append((c,a)); return "ok"
class Bus:
    def __init__(self): self.events=[]
    async def publish(self,e): self.events.append(e)

@pytest.mark.asyncio
async def test_issue_and_pay():
    repo,gateway,bus=InMemoryInvoiceRepository(),Gateway(),Bus()
    svc=BillingApplicationService(repo,gateway,bus)
    customer=uuid.uuid4()
    invoice=await svc.issue_and_pay(customer_id=customer,amount=25)
    assert invoice.status=="paid"
    assert gateway.charges == [(str(customer),25.0)]
    assert [e.name for e in bus.events] == ["billing.invoice.issued","billing.payment.succeeded"]
