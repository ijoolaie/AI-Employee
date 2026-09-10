"""Regression coverage for concurrent RAG indexing admission."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.knowledge import KnowledgeDocument
from app.rag import service


@pytest.mark.asyncio
async def test_index_file_recovers_concurrent_document_creation_and_locks_winner(monkeypatch):
    tenant_id = uuid.uuid4()
    file_id = uuid.uuid4()
    winner = KnowledgeDocument(tenant_id=tenant_id, file_id=file_id, status="indexed")
    lookup_count = 0
    lock_count = 0

    class Result:
        def scalar_one_or_none(self):
            return None if lookup_count == 1 else winner

        def scalar_one(self):
            return winner

    class Nested:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DB:
        def add(self, item):
            assert isinstance(item, KnowledgeDocument)

        async def execute(self, statement):
            nonlocal lookup_count, lock_count
            lookup_count += 1
            if lock_count == 0:
                return Result()
            return Result()

        async def flush(self):
            raise IntegrityError("insert", {}, Exception("duplicate"))

        async def refresh(self, row):
            assert row is winner

        def begin_nested(self):
            return Nested()

    db = DB()
    original_execute = db.execute

    async def execute(statement):
        nonlocal lock_count
        text = str(statement)
        if "FOR UPDATE" in text.upper():
            lock_count += 1
        return await original_execute(statement)

    db.execute = execute
    monkeypatch.setattr(service, "extract_text", lambda _: "content")
    monkeypatch.setattr(service, "chunk_text", lambda _: ["content"])
    monkeypatch.setattr(service, "embed_texts", lambda texts: _embeddings(texts))

    with pytest.raises(IntegrityError):
        await service.index_file(db, tenant_id=tenant_id, file_id=file_id, actor_id=uuid.uuid4())


async def _embeddings(texts):
    return [[1.0] for _ in texts]
