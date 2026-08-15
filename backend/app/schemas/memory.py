from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class MemoryCreateRequest(BaseModel):
    employee_id: UUID
    content: str = Field(min_length=1, max_length=8000)
    memory_type: str = Field(default="fact", pattern="^(fact|preference|instruction|summary)$")
    importance: int = Field(default=3, ge=1, le=5)
    source_run_id: UUID | None = None
    metadata: dict = Field(default_factory=dict)
    expires_at: datetime | None = None
    conflict_key: str | None = Field(default=None, min_length=1, max_length=200)
    supersede_memory_id: UUID | None = None

class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    employee_id: UUID
    memory_type: str
    content: str
    importance: int
    status: str
    metadata_: dict
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int
    supersedes_id: UUID | None

class MemorySearchRequest(BaseModel):
    employee_id: UUID
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.35, ge=0, le=1)

class MemorySearchResult(BaseModel):
    id: UUID
    employee_id: UUID
    memory_type: str
    content: str
    importance: int
    score: float
    metadata: dict
    version: int
    status: str
    supersedes_id: UUID | None
