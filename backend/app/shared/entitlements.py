from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PlanEntitlements:
    employees: int
    runs_per_month: int
    storage_gb: int
    ai_tokens: int
    channels: int
    knowledge_documents: int

def can_consume(current: int, limit: int, amount: int = 1) -> bool:
    return current + amount <= limit
