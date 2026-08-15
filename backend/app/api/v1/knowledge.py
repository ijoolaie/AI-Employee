from uuid import UUID
from fastapi import APIRouter, status
from app.core.deps import DbSession, FileReadContext, FileWriteContext
from app.schemas.common import APIResponse
from app.schemas.knowledge import KnowledgeDocumentResponse, KnowledgeIndexRequest, KnowledgeSearchRequest, KnowledgeSearchResult
from app.rag import service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.post("/index", response_model=APIResponse[KnowledgeDocumentResponse], status_code=status.HTTP_201_CREATED)
async def index_file(payload: KnowledgeIndexRequest, ctx: FileWriteContext, db: DbSession):
    document = await service.index_file(db, tenant_id=ctx.tenant_id, file_id=payload.file_id, actor_id=ctx.user_id)
    return APIResponse(success=True, data=KnowledgeDocumentResponse.model_validate(document))

@router.post("/search", response_model=APIResponse[list[KnowledgeSearchResult]])
async def search(payload: KnowledgeSearchRequest, ctx: FileReadContext, db: DbSession):
    results = await service.search(db, tenant_id=ctx.tenant_id, query=payload.query, top_k=payload.top_k)
    return APIResponse(success=True, data=[KnowledgeSearchResult(**item) for item in results])
