from __future__ import annotations
import uuid
from app.modules.employees.domain.models import EmployeeTask
from app.shared.events import DomainEvent
from app.shared.event_catalog import EMPLOYEE_RUN_COMPLETED

class EmployeesApplicationService:
    def __init__(self, repository, runner, event_bus):
        self.repository,self.runner,self.event_bus=repository,runner,event_bus
    async def run(self, *, employee_id, action, tenant_id=None):
        task=EmployeeTask(uuid.uuid4(),employee_id,action,"running")
        await self.repository.save(task)
        result=await self.runner.run(str(employee_id),action)
        done=EmployeeTask(task.id,employee_id,action,"completed")
        await self.repository.save(done)
        await self.event_bus.publish(DomainEvent(
            name=EMPLOYEE_RUN_COMPLETED, tenant_id=tenant_id,
            payload={"task_id":str(done.id),"employee_id":str(employee_id),"result":result},
        ))
        return done
