from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class KnowledgeIndexRequest(BaseModel):
    file_id: UUID

class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_id: UUID
    status: str
    chunk_count: int
    embedding_model: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)

class KnowledgeSearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    file_id: UUID
    filename: str
    chunk_index: int
    score: float
    content: str
