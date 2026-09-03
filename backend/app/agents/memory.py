"""Bounded memory context for Agent Runtime execution.

The runtime receives a deliberately small, provenance-carrying memory snapshot.
Memory remains tenant/Employee scoped in storage; the EmployeeVersion identity
is bound to the execution contract so a memory snapshot cannot be reused across
an unrelated run context accidentally.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.exceptions import ValidationAppError
from app.memory.context import build_memory_query, memory_settings
from app.memory import service as memory_service

MAX_RUNTIME_MEMORIES = 20
MAX_MEMORY_CONTENT_CHARS = 8000


async def build_runtime_memory(
    db,
    *,
    tenant_id: UUID,
    employee_id: UUID,
    employee_version_id: UUID,
    input_data: dict[str, Any],
    rules: dict[str, Any],
) -> list[dict[str, Any]]:
    """Retrieve a bounded, tenant-safe memory snapshot for one run.

    The storage service performs the authoritative tenant + Employee filter.
    This boundary additionally binds the snapshot to the exact EmployeeVersion
    carried by the AgentRuntimeContract and strips fields that are not useful
    to the model-facing context (notably embeddings and internal metadata).
    """
    config = memory_settings(rules)
    if not config["enabled"]:
        return []

    query = build_memory_query(input_data, config["query_fields"])
    rows = await memory_service.search_memory(
        db,
        tenant_id=tenant_id,
        employee_id=employee_id,
        query=query,
        top_k=min(config["top_k"], MAX_RUNTIME_MEMORIES),
        min_score=config["min_score"],
    )

    snapshot: list[dict[str, Any]] = []
    for row in rows[:MAX_RUNTIME_MEMORIES]:
        row_tenant = row.get("tenant_id")
        row_employee = row.get("employee_id")
        if row_tenant is not None and str(row_tenant) != str(tenant_id):
            raise ValidationAppError("Memory boundary rejected a cross-tenant result")
        if row_employee is not None and str(row_employee) != str(employee_id):
            raise ValidationAppError("Memory boundary rejected a cross-Employee result")

        content = str(row.get("content", "")).strip()
        if not content or len(content) > MAX_MEMORY_CONTENT_CHARS:
            continue
        snapshot.append(
            {
                "id": str(row["id"]),
                "employee_id": str(employee_id),
                "employee_version_id": str(employee_version_id),
                "memory_type": row.get("memory_type", "fact"),
                "content": content,
                "importance": int(row.get("importance", 3)),
                "version": int(row.get("version", 1)),
                "status": "active",
                "score": float(row.get("score", 0.0)),
            }
        )
    return snapshot
