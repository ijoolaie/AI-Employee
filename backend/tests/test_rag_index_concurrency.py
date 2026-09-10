"""Regression coverage for concurrent RAG indexing admission and serialization."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.knowledge import KnowledgeDocument
from app.rag import service


class _Result:
    def __init__(self, one_or_none=None, one=None):
        self._one_or_none = one_or_none
        self._one = one

    def scalar_one_or_none(self):
        return self._one_or_none

    def scalar_one(self):
        return self._one


class _Nested:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.db.added.clear()
        return False


class _FakeDB:
    def __init__(self, file_obj, winner):
        self.file_obj = file_obj
        self.winner = winner
        self.added = []
        self.events = []
        self._doc_lookup_count = 0

    async def execute(self, statement):
        if getattr(statement, "_for_update_arg", None) is not None:
            self.events.append("lock")
            return _Result(one=self.winner)
        if "file_object" in statement.column_descriptions[0]["entity"].__name__.lower():
            self.events.append("file")
            return _Result(one_or_none=self.file_obj)
        if self._doc_lookup_count == 0:
            self._doc_lookup_count += 1
            self.events.append("doc-miss")
            return _Result(one_or_none=None)
        self.events.append("doc-recovery")
        return _Result(one_or_none=self.winner)

    def add(self, item):
        self.added.append(item)
        self.events.append("add")

    async def flush(self):
        self.events.append("flush")
        if self.events.count("flush") == 1:
            raise IntegrityError("insert", {}, Exception("duplicate"))

    def begin_nested(self):
        return _Nested(self)

    async def refresh(self, row):
        assert row is self.winner
        self.events.append("refresh")


@pytest.mark.asyncio
async def test_index_file_recovers_concurrent_document_creation_and_locks_winner(monkeypatch):
    tenant_id = uuid.uuid4()
    file_id = uuid.uuid4()
    file_obj = type(
        "FileObject",
        (),
        {"id": file_id, "tenant_id": tenant_id, "status": "active", "filename": "note.txt"},
    )()
    winner = KnowledgeDocument(tenant_id=tenant_id, file_id=file_id, status="pending")
    db = _FakeDB(file_obj, winner)

    monkeypatch.setattr(service, "extract_text", lambda _: "content")
    monkeypatch.setattr(service, "chunk_text", lambda _: ["content"])

    async def embeddings(texts):
        return [[1.0] for _ in texts]

    monkeypatch.setattr(service, "embed_texts", embeddings)
    monkeypatch.setattr(
        service.audit_service if hasattr(service, "audit_service") else __import__("app.services.audit_service", fromlist=["record"]),
        "record",
        lambda *args, **kwargs: None,
    )

    class _Audit:
        async def record(self, *args, **kwargs):
            return None

    monkeypatch.setattr(service, "audit_service", _Audit(), raising=False)

    result = await service.index_file(
        db,
        tenant_id=tenant_id,
        file_id=file_id,
        actor_id=uuid.uuid4(),
    )

    assert result is winner
    assert winner.status == "indexed"
    assert winner.chunk_count == 1
    assert "doc-miss" in db.events
    assert "doc-recovery" in db.events
    assert "lock" in db.events
    assert db.events.index("lock") < db.events.index("add")


@pytest.mark.asyncio
async def test_index_file_locks_existing_document_before_replacing_chunks(monkeypatch):
    tenant_id = uuid.uuid4()
    file_id = uuid.uuid4()
    file_obj = type(
        "FileObject",
        (),
        {"id": file_id, "tenant_id": tenant_id, "status": "active", "filename": "note.txt"},
    )()
    document = KnowledgeDocument(tenant_id=tenant_id, file_id=file_id, status="indexed")
    db = _FakeDB(file_obj, document)
    db._doc_lookup_count = 1

    monkeypatch.setattr(service, "extract_text", lambda _: "content")
    monkeypatch.setattr(service, "chunk_text", lambda _: ["content"])

    async def embeddings(texts):
        return [[1.0] for _ in texts]

    monkeypatch.setattr(service, "embed_texts", embeddings)

    class _Audit:
        async def record(self, *args, **kwargs):
            return None

    monkeypatch.setattr(service, "audit_service", _Audit(), raising=False)

    result = await service.index_file(
        db,
        tenant_id=tenant_id,
        file_id=file_id,
        actor_id=uuid.uuid4(),
    )

    assert result is document
    assert document.status == "indexed"
    assert db.events.index("lock") < db.events.index("add")
