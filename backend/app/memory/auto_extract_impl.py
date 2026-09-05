"""Automatic Employee-memory extraction and conservative consolidation.

This layer is deliberately best-effort: a memory extraction failure must never
turn an otherwise successful Employee Run into a failed Run. Candidates are
created only when the EmployeeVersion explicitly enables auto_extract.
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ai.gateway import AIGateway
from app.ai.schemas import ChatMessage, ChatRequest
from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.core.logging import request_id_var
from app.models.memory import EmployeeMemory
from app.rag.service import embed_texts, cosine_similarity
from app.services import audit_service
from app.memory.service import create_memory

settings = get_settings()

_MEMORY_TYPES = {"fact", "preference", "instruction", "summary"}
_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)
_SECRET_RE = re.compile(r"(?:password|passwd|api[_ -]?key|access[_ -]?token|refresh[_ -]?token|secret)\s*[:=]", re.IGNORECASE)


def auto_memory_settings(rules: dict[str, Any]) -> dict[str, Any]:
    raw = rules.get("memory", {}) if isinstance(rules, dict) else {}
    if not isinstance(raw, dict) or not raw.get("enabled", False) or not raw.get("auto_extract", False):
        return {"enabled": False, "max_candidates": 0, "min_importance": 0, "dedup_threshold": 1.0, "conflict_resolution": "supersede"}
    max_candidates = raw.get("max_candidates", 5)
    min_importance = raw.get("min_importance", 3)
    dedup_threshold = raw.get("dedup_threshold", 0.92)
    if not isinstance(max_candidates, int) or isinstance(max_candidates, bool) or not 1 <= max_candidates <= 10:
        raise ValidationAppError("memory.max_candidates must be between 1 and 10")
    if not isinstance(min_importance, int) or isinstance(min_importance, bool) or not 1 <= min_importance <= 5:
        raise ValidationAppError("memory.min_importance must be between 1 and 5")
    if not isinstance(dedup_threshold, (int, float)) or isinstance(dedup_threshold, bool) or not 0.80 <= float(dedup_threshold) <= 0.99:
        raise ValidationAppError("memory.dedup_threshold must be between 0.80 and 0.99")
    return {"enabled": True, "max_candidates": max_candidates, "min_importance": min_importance, "dedup_threshold": float(dedup_threshold), "conflict_resolution": str(raw.get("conflict_resolution", "supersede"))}


def _parse_candidates(text: str, max_candidates: int, min_importance: int) -> list[dict[str, Any]]:
    raw = text.strip()
    match = _FENCE_RE.match(raw)
    if match:
        raw = match.group(1).strip()
    data = json.loads(raw)
    if isinstance(data, dict):
        data = data.get("memories", [])
    if not isinstance(data, list):
        raise ValueError("Memory extractor response must be a JSON array")
    candidates: list[dict[str, Any]] = []
    for item in data[:max_candidates]:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content", "")).strip()
        memory_type = str(item.get("memory_type", "fact")).strip().lower()
        importance = item.get("importance", min_importance)
        if memory_type not in _MEMORY_TYPES or not content or len(content) > 2000:
            continue
        if _SECRET_RE.search(content):
            continue
        if not isinstance(importance, int) or isinstance(importance, bool):
            continue
        importance = max(1, min(5, importance))
        if importance < min_importance:
            continue
        subject_key = str(item.get("subject_key", "")).strip()[:200] or None
        candidates.append({"content": content, "memory_type": memory_type, "importance": importance, "subject_key": subject_key})
    return candidates


async def _find_duplicate(db: AsyncSession, *, tenant_id: uuid.UUID, employee_id: uuid.UUID, content: str, memory_type: str, threshold: float) -> tuple[EmployeeMemory | None, float]:
    query_embedding = (await embed_texts([content]))[0]
    result = await db.execute(
        select(EmployeeMemory).where(
            EmployeeMemory.tenant_id == tenant_id,
            EmployeeMemory.employee_id == employee_id,
            EmployeeMemory.memory_type == memory_type,
            EmployeeMemory.status == "active",
        )
    )
    best: tuple[EmployeeMemory | None, float] = (None, 0.0)
    for memory in result.scalars().all():
        score = cosine_similarity(query_embedding, memory.embedding)
        if score >= threshold and score > best[1]:
            best = (memory, score)
    return best


async def extract_and_consolidate_run_memory(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    run_id: uuid.UUID,
    input_data: dict[str, Any],
    output_text: str,
    rules: dict[str, Any],
) -> dict[str, int]:
    config = auto_memory_settings(rules)
    if not config["enabled"]:
        return {"candidates": 0, "created": 0, "consolidated": 0, "skipped": 0}

    source = json.dumps({"input": input_data, "output": output_text[:8000]}, ensure_ascii=False, default=str)
    request = ChatRequest(
        model=settings.ai_default_model,
        max_tokens=900,
        temperature=0.1,
        messages=[
            ChatMessage(
                role="system",
                content=(
                    "You are an Employee memory extractor. Extract only durable information "
                    "that is useful in future runs: stable facts, explicit preferences, durable "
                    "instructions, or concise summaries. Do not store secrets, credentials, tokens, "
                    "or one-off conversational filler. Return ONLY valid JSON in this shape: "
                    '{"memories":[{"memory_type":"fact|preference|instruction|summary",'
                    '"content":"...","importance":1-5,"subject_key":"stable topic key or null"}]} .'
                ),
            ),
            ChatMessage(role="user", content=source),
        ],
    )
    gateway = AIGateway()
    result = await gateway.chat(
        db,
        request,
        tenant_id=tenant_id,
        run_id=run_id,
        prompt_version="memory-extractor-v1",
        call_metadata={"purpose": "memory_extraction", "max_candidates": config["max_candidates"]},
    )
    candidates = _parse_candidates(result.content, config["max_candidates"], config["min_importance"])
    stats = {"candidates": len(candidates), "created": 0, "consolidated": 0, "skipped": 0}

    for candidate in candidates:
        should_supersede = False
        existing, score = await _find_duplicate(
            db,
            tenant_id=tenant_id,
            employee_id=employee_id,
            content=candidate["content"],
            memory_type=candidate["memory_type"],
            threshold=config["dedup_threshold"],
        )
        conflict_key = candidate.get("subject_key")
        if conflict_key:
            keyed = await db.execute(select(EmployeeMemory).where(
                EmployeeMemory.tenant_id == tenant_id,
                EmployeeMemory.employee_id == employee_id,
                EmployeeMemory.memory_type == candidate["memory_type"],
                EmployeeMemory.status == "active",
            ))
            for memory in keyed.scalars().all():
                if str((memory.metadata_ or {}).get("conflict_key", "")) == conflict_key:
                    similarity = cosine_similarity((await embed_texts([candidate["content"]]))[0], memory.embedding)
                    existing = memory
                    score = max(score, similarity)
                    should_supersede = similarity < config["dedup_threshold"]
                    break
        if existing is None:
            await create_memory(
                db,
                tenant_id=tenant_id,
                employee_id=employee_id,
                content=candidate["content"],
                memory_type=candidate["memory_type"],
                importance=candidate["importance"],
                source_run_id=run_id,
                metadata={"source": "automatic_extraction", "extractor": "memory-extractor-v1", **({"conflict_key": candidate["subject_key"]} if candidate.get("subject_key") else {})},
            )
            stats["created"] += 1
            continue

        # Exact subject keys represent the same durable topic. Create a new
        # version and supersede the old one so historical state remains auditable.
        if candidate.get("subject_key") and should_supersede:
            await create_memory(
                db,
                tenant_id=tenant_id,
                employee_id=employee_id,
                content=candidate["content"],
                memory_type=candidate["memory_type"],
                importance=candidate["importance"],
                source_run_id=run_id,
                metadata={"source": "automatic_consolidation", "extractor": "memory-extractor-v1", "conflict_key": candidate["subject_key"], "previous_similarity": round(score, 6)},
                supersede_memory_id=existing.id,
            )
            stats["consolidated"] += 1
        else:
            # Semantic duplicates are still updated conservatively in place.
            new_content = candidate["content"]
            if candidate["importance"] > existing.importance or len(new_content) > len(existing.content):
                existing.content = new_content
                existing.embedding = (await embed_texts([new_content]))[0]
                existing.importance = max(existing.importance, candidate["importance"])
                existing.source_run_id = run_id
                existing.metadata_ = {
                    **(existing.metadata_ or {}),
                    "source": "automatic_consolidation",
                    "last_consolidated_score": round(score, 6),
                }
                stats["consolidated"] += 1

    await db.flush()
    await audit_service.record(
        db,
        action="memory.auto_extracted",
        actor_type="system",
        tenant_id=tenant_id,
        resource_type="run",
        resource_id=run_id,
        status="success",
        request_id=request_id_var.get(),
        metadata=stats,
    )
    return stats
