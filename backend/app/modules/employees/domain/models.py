from dataclasses import dataclass
import uuid
@dataclass(frozen=True)
class EmployeeTask:
    id: uuid.UUID
    employee_id: uuid.UUID
    action: str
    status: str
