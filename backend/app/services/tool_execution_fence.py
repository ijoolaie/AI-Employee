"""Durable fences for side-effecting Agent tool execution.

The fence is committed independently from the Run transaction. Once a tool
crosses this boundary, a later redelivery cannot blindly execute it again.
Unknown outcomes therefore fail closed rather than replaying an external side
effect.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import AsyncSessionLocal
from app.core.exceptions import ValidationAppError
from app.models.tool_execution_fence import ToolExecutionFence


async def begin_tool_execution_fence(
    *,
    tenant_id: uuid.UUID,
    run_id: uuid.UUID,
    tool_call_id: str,
    tool_name: str,
) -> uuid.UUID:
    """Durably reserve one logical side-effecting tool invocation."""
    if not tool_call_id:
        raise ValidationAppError(
            "Side-effecting Agent tool execution requires a stable tool_call_id"
        )

    fence_id = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"aiep:tool-execution:{tenant_id}:{run_id}:{tool_call_id}",
    )
    async with AsyncSessionLocal() as db:
        existing = await db.get(ToolExecutionFence, fence_id)
        if existing is not None:
            raise ValidationAppError(
                "Tool execution already crossed the side-effect boundary; refusing blind replay",
                details={
                    "tool": tool_name,
                    "tool_call_id": tool_call_id,
                    "status": existing.status,
                },
            )
        db.add(
            ToolExecutionFence(
                id=fence_id,
                tenant_id=tenant_id,
                run_id=run_id,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                status="in_flight",
            )
        )
        try:
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            raise ValidationAppError(
                "Concurrent tool execution crossed the side-effect boundary; refusing blind replay",
                details={"tool": tool_name, "tool_call_id": tool_call_id},
            ) from exc
    return fence_id


async def complete_tool_execution_fence(
    fence_id: uuid.UUID,
    *
) -> None:
    """Mark the side-effect as durably completed after the handler returns."""
    async with AsyncSessionLocal() as db:
        fence = await db.get(ToolExecutionFence, fence_id)
        if fence is None:
            raise RuntimeError("Tool execution fence disappeared")
        fence.status = "success"
        fence.completed_at = datetime.now(timezone.utc)
        await db.commit()


async def mark_tool_execution_unknown(
    fence_id: uuid.UUID,
    error_message: str,
) -> None:
    """Persist an ambiguous outcome; automatic replay remains prohibited."""
    async with AsyncSessionLocal() as db:
        fence = await db.get(ToolExecutionFence, fence_id)
        if fence is None:
            return
        fence.status = "unknown"
        fence.error_message = error_message[:1000]
        fence.completed_at = datetime.now(timezone.utc)
        await db.commit()


async def get_tool_execution_fence(
    *,
    tenant_id: uuid.UUID,
    run_id: uuid.UUID,
    tool_call_id: str,
) -> ToolExecutionFence | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ToolExecutionFence).where(
                ToolExecutionFence.tenant_id == tenant_id,
                ToolExecutionFence.run_id == run_id,
                ToolExecutionFence.tool_call_id == tool_call_id,
            )
        )
        return result.scalar_one_or_none()
