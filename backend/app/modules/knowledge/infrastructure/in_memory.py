from __future__ import annotations
from app.modules.knowledge.domain.models import KnowledgeDocument, KnowledgeChunk

class InMemoryDocumentRepository:
    def __init__(self):
        self.documents = {}

    async def save_document(self, document):
        self.documents[str(document.id)] = document
        return document

    async def get_document(self, document_id, tenant_id):
        document = self.documents.get(document_id)
        if document is None or document.tenant_id != tenant_id:
            return None
        return document

class InMemoryChunkRepository:
    def __init__(self):
        self.chunks = []

    async def save_chunks(self, chunks):
        self.chunks.extend(chunks)
        return chunks
