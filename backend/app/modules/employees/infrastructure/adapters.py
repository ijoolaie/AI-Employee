class LegacyEmployeeRunner:
    def __init__(self, legacy_service): self.legacy_service=legacy_service
    async def run(self, employee_id, action):
        return await self.legacy_service.run(employee_id, action)

class InMemoryEmployeeTaskRepository:
    def __init__(self): self.items={}
    async def save(self, task):
        self.items[str(task.id)]=task
        return task
