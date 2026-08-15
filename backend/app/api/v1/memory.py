from uuid import UUID
from fastapi import APIRouter, status
from app.core.deps import DbSession, MemoryDeleteContext, MemoryReadContext, MemoryWriteContext
from app.schemas.common import APIResponse
from app.schemas.memory import MemoryCreateRequest, MemoryResponse, MemorySearchRequest, MemorySearchResult
from app.memory import service

router = APIRouter(prefix="/memory", tags=["memory"])

@router.post("", response_model=APIResponse[MemoryResponse], status_code=status.HTTP_201_CREATED)
async def create_memory(payload: MemoryCreateRequest, ctx: MemoryWriteContext, db: DbSession):
    memory = await service.create_memory(db, tenant_id=ctx.tenant_id, employee_id=payload.employee_id, content=payload.content, memory_type=payload.memory_type, importance=payload.importance, source_run_id=payload.source_run_id, metadata={**payload.metadata, **({"conflict_key": payload.conflict_key} if payload.conflict_key else {})}, expires_at=payload.expires_at, actor_id=ctx.user_id, supersede_memory_id=payload.supersede_memory_id)
    return APIResponse(success=True, data=MemoryResponse.model_validate(memory))

@router.post("/search", response_model=APIResponse[list[MemorySearchResult]])
async def search_memory(payload: MemorySearchRequest, ctx: MemoryReadContext, db: DbSession):
    results = await service.search_memory(db, tenant_id=ctx.tenant_id, employee_id=payload.employee_id, query=payload.query, top_k=payload.top_k, min_score=payload.min_score)
    return APIResponse(success=True, data=[MemorySearchResult(**item) for item in results])

@router.delete("/{memory_id}", response_model=APIResponse[None])
async def delete_memory(memory_id: UUID, ctx: MemoryDeleteContext, db: DbSession):
    await service.delete_memory(db, tenant_id=ctx.tenant_id, memory_id=memory_id, actor_id=ctx.user_id)
    return APIResponse(success=True, data=None)
