import uuid
import pytest
from app.modules.employees.application.service import EmployeesApplicationService
from app.modules.employees.infrastructure.adapters import InMemoryEmployeeTaskRepository

class Runner:
    async def run(self,e,a): return {"ok":True}
class Bus:
    def __init__(self): self.events=[]
    async def publish(self,e): self.events.append(e)

@pytest.mark.asyncio
async def test_employee_run():
    repo,bus=InMemoryEmployeeTaskRepository(),Bus()
    svc=EmployeesApplicationService(repo,Runner(),bus)
    task=await svc.run(employee_id=uuid.uuid4(),action="report")
    assert task.status=="completed"
    assert bus.events[0].name=="employee.run.completed"
