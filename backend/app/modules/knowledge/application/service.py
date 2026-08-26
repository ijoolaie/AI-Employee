from __future__ import annotations
from typing import Any
import uuid

from app.shared.events import DomainEvent
from app.shared.event_catalog import DOCUMENT_INGESTED
from app.modules.knowledge.domain.models import KnowledgeChunk, KnowledgeDocument
from app.modules.knowledge.domain.ports import (
    DocumentParser,
    DocumentRepository,
    ChunkRepository,
    EmbeddingProvider,
)

class KnowledgeApplicationService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
        parser: DocumentParser,
        embedding_provider: EmbeddingProvider,
        event_bus,
    ) -> None:
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.parser = parser
        self.embedding_provider = embedding_provider
        self.event_bus = event_bus

    async def ingest(
        self,
        *,
        source: str,
        title: str,
        tenant_id: uuid.UUID,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        if tenant_id is None:
            raise ValueError("tenant_id is required for knowledge ingestion")

        document = KnowledgeDocument(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title=title,
            source=source,
            status="processing",
            metadata=metadata or {},
        )
        await self.document_repository.save_document(document)

        parsed = await self.parser.parse(source)
        texts = [item.get("text", "") for item in parsed if item.get("text")]
        vectors = await self.embedding_provider.embed(texts) if texts else []

        chunks = [
            KnowledgeChunk(
                id=uuid.uuid4(),
                document_id=document.id,
                text=text,
                metadata=parsed[i].get("metadata", {}),
                embedding_ref=f"pending:{i}",
            )
            for i, text in enumerate(texts)
        ]
        await self.chunk_repository.save_chunks(chunks)

        completed = KnowledgeDocument(
            id=document.id,
            tenant_id=document.tenant_id,
            title=document.title,
            source=document.source,
            status="ready",
            metadata={**document.metadata, "chunk_count": len(chunks), "embedding_count": len(vectors)},
        )
        await self.document_repository.save_document(completed)

        await self.event_bus.publish(
            DomainEvent(
                name=DOCUMENT_INGESTED,
                tenant_id=tenant_id,
                payload={
                    "document_id": str(completed.id),
                    "chunk_count": len(chunks),
                },
            )
        )
        return completed
