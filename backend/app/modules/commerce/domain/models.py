from dataclasses import dataclass
from typing import Any
import uuid

@dataclass(frozen=True)
class Order:
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    customer_id: uuid.UUID
    status: str
    items: list[dict[str, Any]]
    total: float
