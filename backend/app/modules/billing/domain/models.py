from dataclasses import dataclass
import uuid

@dataclass(frozen=True)
class Invoice:
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    customer_id: uuid.UUID
    amount: float
    status: str
