from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any
import uuid

@dataclass(frozen=True)
class KnowledgeDocument:
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    title: str
    source: str
    status: str
    metadata: dict[str, Any]

@dataclass(frozen=True)
class KnowledgeChunk:
    id: uuid.UUID
    document_id: uuid.UUID
    text: str
    metadata: dict[str, Any]
    embedding_ref: str | None = None
