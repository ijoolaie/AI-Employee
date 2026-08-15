from typing import Protocol, Any

class EmployeeModule(Protocol):
    slug: str
    name: str
    version: str

    async def execute(self, **kwargs: Any) -> Any:
        ...
