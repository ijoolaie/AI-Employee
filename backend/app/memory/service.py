"""Employee memory storage, semantic retrieval, and lifecycle/version management."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.logging import request_id_var
from app.models.employee import Employee
from app.models.memory import EmployeeMemory
from app.rag.service import embed_texts, cosine_similarity
from app.services import audit_service

_MEMORY_TYPES = {"fact", "preference", "instruction", "summary"}
_MEMORY_STATUSES = {"active", "superseded", "expired", "deleted", "conflict"}


def _validate_expiry(expires_at: datetime | None) -> None:
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        raise ValidationAppError("expires_at must be in the future")


def _active_clause(now: datetime):
    return (EmployeeMemory.status == "active") & ((EmployeeMemory.expires_at.is_(None)) | (EmployeeMemory.expires_at > now))


async def create_memory(
    db: AsyncSession, *, tenant_id: uuid.UUID, employee_id: uuid.UUID, content: str,
    memory_type: str = "fact", importance: int = 3, source_run_id: uuid.UUID | None = None,
    metadata: dict | None = None, expires_at: datetime | None = None,
    actor_id: uuid.UUID | None = None, supersede_memory_id: uuid.UUID | None = None,
) -> EmployeeMemory:
    employee = (await db.execute(select(Employee).where(Employee.id == employee_id, or_(Employee.tenant_id == tenant_id, Employee.tenant_id.is_(None))))).scalar_one_or_none()
    if employee is None:
        raise NotFoundError("Employee not found")
    content = content.strip()
    if not content or len(content) > 8000:
        raise ValidationAppError("Memory content must contain 1 to 8000 characters")
    if memory_type not in _MEMORY_TYPES:
        raise ValidationAppError("Unsupported memory_type")
    if not 1 <= importance <= 5:
        raise ValidationAppError("Memory importance must be between 1 and 5")
    _validate_expiry(expires_at)

    metadata = dict(metadata or {})
    conflict_key = str(metadata.get("conflict_key", "")).strip() or None
    previous: EmployeeMemory | None = None
    if supersede_memory_id:
        previous = (await db.execute(select(EmployeeMemory).where(EmployeeMemory.id == supersede_memory_id, EmployeeMemory.tenant_id == tenant_id, EmployeeMemory.employee_id == employee_id))).scalar_one_or_none()
        if previous is None:
            raise NotFoundError("Memory to supersede not found")
        if previous.status not in {"active", "conflict"}:
            raise ValidationAppError("Only active/conflict memories can be superseded")
    elif conflict_key:
        result = await db.execute(select(EmployeeMemory).where(EmployeeMemory.tenant_id == tenant_id, EmployeeMemory.employee_id == employee_id, EmployeeMemory.memory_type == memory_type, _active_clause(datetime.now(timezone.utc))))
        for candidate in result.scalars().all():
            if str((candidate.metadata_ or {}).get("conflict_key", "")) == conflict_key:
                previous = candidate
                break

    embedding = (await embed_texts([content]))[0]
    next_version = (previous.version + 1) if previous else 1
    effective_at = datetime.now(timezone.utc)
    memory = EmployeeMemory(
        tenant_id=tenant_id, employee_id=employee_id, source_run_id=source_run_id,
        supersedes_id=previous.id if previous else None, memory_type=memory_type,
        content=content, embedding=embedding, importance=importance, version=next_version,
        status="active", metadata_=metadata, effective_at=effective_at, expires_at=expires_at, created_by=actor_id,
    )
    db.add(memory)
    await db.flush()

    if previous:
        previous.status = "superseded"
        await audit_service.record(db, action="memory.superseded", actor_type="user" if actor_id else "system", actor_id=actor_id, tenant_id=tenant_id, resource_type="employee_memory", resource_id=previous.id, request_id=request_id_var.get(), metadata={"replacement_id": str(memory.id), "version": previous.version})

    await audit_service.record(db, action="memory.created", actor_type="user" if actor_id else "system", actor_id=actor_id, tenant_id=tenant_id, resource_type="employee_memory", resource_id=memory.id, request_id=request_id_var.get(), metadata={"employee_id": str(employee_id), "memory_type": memory_type, "importance": importance, "version": next_version, "supersedes_id": str(previous.id) if previous else None})
    return memory


async def expire_due_memories(db: AsyncSession, *, tenant_id: uuid.UUID | None = None) -> int:
    now = datetime.now(timezone.utc)
    stmt = select(EmployeeMemory).where(EmployeeMemory.status == "active", EmployeeMemory.expires_at.is_not(None), EmployeeMemory.expires_at <= now)
    if tenant_id is not None:
        stmt = stmt.where(EmployeeMemory.tenant_id == tenant_id)
    result = await db.execute(stmt)
    memories = list(result.scalars().all())
    for memory in memories:
        memory.status = "expired"
        await audit_service.record(db, action="memory.expired", actor_type="system", tenant_id=memory.tenant_id, resource_type="employee_memory", resource_id=memory.id, request_id=request_id_var.get(), metadata={"employee_id": str(memory.employee_id), "version": memory.version})
    if memories:
        await db.flush()
    return len(memories)


async def search_memory(db: AsyncSession, *, tenant_id: uuid.UUID, employee_id: uuid.UUID, query: str, top_k: int = 5, min_score: float = 0.35) -> list[dict]:
    if not query.strip():
        raise ValidationAppError("Memory query must not be empty")
    await expire_due_memories(db, tenant_id=tenant_id)
    query_embedding = (await embed_texts([query]))[0]
    now = datetime.now(timezone.utc)
    result = await db.execute(select(EmployeeMemory).where(EmployeeMemory.tenant_id == tenant_id, EmployeeMemory.employee_id == employee_id, _active_clause(now)))
    scored = []
    for memory in result.scalars().all():
        score = cosine_similarity(query_embedding, memory.embedding)
        if score >= min_score:
            scored.append((score, memory))
    scored.sort(key=lambda item: (item[0], item[1].importance, item[1].version), reverse=True)
    return [{"id": str(m.id), "employee_id": str(m.employee_id), "memory_type": m.memory_type, "content": m.content, "importance": m.importance, "version": m.version, "status": m.status, "supersedes_id": str(m.supersedes_id) if m.supersedes_id else None, "score": round(score, 6), "metadata": m.metadata_} for score, m in scored[:max(1, min(top_k, 20))]]


async def delete_memory(db: AsyncSession, *, tenant_id: uuid.UUID, memory_id: uuid.UUID, actor_id: uuid.UUID) -> None:
    memory = (await db.execute(select(EmployeeMemory).where(EmployeeMemory.id == memory_id, EmployeeMemory.tenant_id == tenant_id))).scalar_one_or_none()
    if memory is None:
        raise NotFoundError("Memory not found")
    memory.status = "deleted"
    await db.flush()
    await audit_service.record(db, action="memory.deleted", actor_type="user", actor_id=actor_id, tenant_id=tenant_id, resource_type="employee_memory", resource_id=memory.id, request_id=request_id_var.get(), metadata={"employee_id": str(memory.employee_id), "version": memory.version})
