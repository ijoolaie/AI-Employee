import uuid
import pytest

from app.modules.knowledge.application.service import KnowledgeApplicationService
from app.modules.knowledge.infrastructure.in_memory import (
    InMemoryDocumentRepository,
    InMemoryChunkRepository,
)

class FakeParser:
    async def parse(self, source):
        return [
            {"text": "hello world", "metadata": {"page": 1}},
            {"text": "second chunk", "metadata": {"page": 2}},
        ]

class FakeEmbeddings:
    async def embed(self, texts):
        return [[0.1, 0.2] for _ in texts]

class FakeBus:
    def __init__(self):
        self.events = []
    async def publish(self, event):
        self.events.append(event)

@pytest.mark.asyncio
async def test_knowledge_ingestion_creates_document_chunks_and_event():
    docs = InMemoryDocumentRepository()
    chunks = InMemoryChunkRepository()
    bus = FakeBus()

    service = KnowledgeApplicationService(
        document_repository=docs,
        chunk_repository=chunks,
        parser=FakeParser(),
        embedding_provider=FakeEmbeddings(),
        event_bus=bus,
    )

    tenant_id = uuid.uuid4()
    document = await service.ingest(
        source="file://book.pdf",
        title="Book",
        tenant_id=tenant_id,
    )

    assert document.status == "ready"
    assert document.tenant_id == tenant_id
    assert document.metadata["chunk_count"] == 2
    assert len(chunks.chunks) == 2
    assert len(bus.events) == 1
    assert bus.events[0].name == "knowledge.document.ingested"
    assert await docs.get_document(str(document.id), tenant_id) == document

@pytest.mark.asyncio
async def test_knowledge_document_cannot_be_read_by_another_tenant():
    docs = InMemoryDocumentRepository()
    chunks = InMemoryChunkRepository()
    bus = FakeBus()
    service = KnowledgeApplicationService(
        document_repository=docs,
        chunk_repository=chunks,
        parser=FakeParser(),
        embedding_provider=FakeEmbeddings(),
        event_bus=bus,
    )

    owner_tenant = uuid.uuid4()
    other_tenant = uuid.uuid4()
    document = await service.ingest(
        source="file://private.pdf",
        title="Private",
        tenant_id=owner_tenant,
    )

    assert await docs.get_document(str(document.id), owner_tenant) == document
    assert await docs.get_document(str(document.id), other_tenant) is None

@pytest.mark.asyncio
async def test_knowledge_ingestion_rejects_missing_tenant_context():
    service = KnowledgeApplicationService(
        document_repository=InMemoryDocumentRepository(),
        chunk_repository=InMemoryChunkRepository(),
        parser=FakeParser(),
        embedding_provider=FakeEmbeddings(),
        event_bus=FakeBus(),
    )

    with pytest.raises(ValueError, match="tenant_id is required"):
        await service.ingest(source="file://private.pdf", title="Private", tenant_id=None)
