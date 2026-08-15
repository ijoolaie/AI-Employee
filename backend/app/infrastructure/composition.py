from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Infrastructure:
    repository_factory: Any
    unit_of_work_factory: Any
    task_queue: Any
    event_bus: Any
    object_storage: Any
    ai_provider: Any
    payment_gateway: Any
    commerce_provider: Any
