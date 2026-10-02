"""Governed sales engagement events and attribution.

Uses the immutable tenant audit ledger as the durable event store. Event
creation is idempotent under the tenant ledger advisory lock, so provider
replays cannot create duplicate engagement events.
"""
from __future__ import annotations

import uuid
from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.services import audit_service


EVENT_ACTION = "sales.engagement"


async def record_event(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    event_key: str,
    event_type: str,
    tool_call_id: str | None = None,
    outbox_id: str | None = None,
    provider_message_id: str | None = None,
    deal_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Persist one immutable, tenant-scoped engagement event exactly once."""
    if not event_key or len(event_key) > 255:
        raise ValueError("event_key is required and must be <=255 characters")
    if not event_type or len(event_type) > 80:
        raise ValueError("event_type is required and must be <=80 characters")

    # audit_service.record acquires the tenant ledger advisory lock. Holding
    # that lock while checking the event makes the check+insert linearizable.
    existing = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.ledger_scope == str(tenant_id),
            AuditLog.action == EVENT_ACTION,
            AuditLog.resource_type == "sales_engagement",
            AuditLog.metadata_.op("->>")("event_key") == event_key,
        )
        .limit(1)
    )
    found = existing.scalar_one_or_none()
    if found is not None:
        return found

    entry = await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_type="system",
        action=EVENT_ACTION,
        resource_type="sales_engagement",
        resource_id=deal_id or event_key,
        metadata={
            "event_key": event_key,
            "event_type": event_type,
            "tool_call_id": tool_call_id,
            "outbox_id": outbox_id,
            "provider_message_id": provider_message_id,
            "deal_id": deal_id,
            **(metadata or {}),
        },
    )
    return entry


async def record_outreach_delivered(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    tool_call_id: str,
    outbox_id: str,
    provider_message_id: str,
    recipients: list[str],
    subject: str,
    deal_id: str | None = None,
) -> AuditLog:
    return await record_event(
        db,
        tenant_id=tenant_id,
        event_key=f"delivered:{outbox_id}",
        event_type="outreach_delivered",
        tool_call_id=tool_call_id,
        outbox_id=outbox_id,
        provider_message_id=provider_message_id,
        metadata={"recipient_count": len(recipients), "subject": subject, "deal_id": deal_id},
    )


async def record_outreach_response(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    event_key: str,
    response_text: str,
    tool_call_id: str | None = None,
    outbox_id: str | None = None,
    provider_message_id: str | None = None,
    deal_id: str | None = None,
    source: str = "synthetic",
) -> AuditLog:
    return await record_event(
        db,
        tenant_id=tenant_id,
        event_key=event_key,
        event_type="outreach_response",
        tool_call_id=tool_call_id,
        outbox_id=outbox_id,
        provider_message_id=provider_message_id,
        deal_id=deal_id,
        metadata={"source": source, "response_text": response_text},
    )


async def attribution_summary(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    deal_id: str | None = None,
) -> dict[str, Any]:
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.action == EVENT_ACTION,
            AuditLog.resource_type == "sales_engagement",
        )
        .order_by(AuditLog.created_at.asc())
    )
    if deal_id:
        stmt = stmt.where(AuditLog.metadata_.op("->>")("deal_id") == str(deal_id))
    rows = list((await db.execute(stmt)).scalars().all())
    types = {str((r.metadata_ or {}).get("event_type")) for r in rows}
    return {
        "sent": int("outreach_queued" in types or "outreach_delivered" in types),
        "delivered": int("outreach_delivered" in types),
        "responded": int("outreach_response" in types),
        "event_count": len(rows),
        "event_types": sorted(types),
        "deal_id": deal_id,
    }
