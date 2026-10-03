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
    sender_email: str | None = None,
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
        metadata={
            "source": source,
            "response_text": response_text,
            "sender_email": sender_email,
        },
    )


async def ingest_outreach_response(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    event_key: str,
    provider_message_id: str,
    response_text: str,
    source: str,
    sender_email: str | None = None,
) -> AuditLog:
    """Ingest a provider response only when it correlates to a delivered event.

    Correlation is derived from the immutable delivery ledger; callers cannot
    supply or override deal_id, outbox_id, or tool_call_id.
    """
    if not response_text or len(response_text) > 8000:
        raise ValueError("response_text is required and must be <=8000 characters")

    existing_response = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.action == EVENT_ACTION,
            AuditLog.resource_type == "sales_engagement",
            AuditLog.metadata_.op("->>")("event_key") == event_key,
        )
        .limit(1)
    )
    existing = existing_response.scalar_one_or_none()
    if existing is not None:
        existing_metadata = existing.metadata_ or {}
        if existing_metadata.get("provider_message_id") != provider_message_id:
            raise ValueError("Inbound event key is already bound to another provider message")
        return existing

    delivery_result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.action == EVENT_ACTION,
            AuditLog.resource_type == "sales_engagement",
            AuditLog.metadata_.op("->>")("event_type") == "outreach_delivered",
            AuditLog.metadata_.op("->>")("provider_message_id") == provider_message_id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )
    delivery = delivery_result.scalar_one_or_none()
    if delivery is None:
        raise ValueError("Inbound provider message does not correlate to a delivered outreach")

    delivery_metadata = delivery.metadata_ or {}
    return await record_outreach_response(
        db,
        tenant_id=tenant_id,
        event_key=event_key,
        response_text=response_text,
        tool_call_id=delivery_metadata.get("tool_call_id"),
        outbox_id=delivery_metadata.get("outbox_id"),
        provider_message_id=provider_message_id,
        deal_id=delivery_metadata.get("deal_id"),
        source=source,
        sender_email=sender_email,
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
