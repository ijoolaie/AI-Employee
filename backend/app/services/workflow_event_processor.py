"""Workflow event processing orchestration.

Keeps event ingestion separate from workflow execution. A delivery is resolved
into a durable WorkflowRun and then handed to the normal execution pipeline.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.services import workflow_service, outbox_service, audit_service
from app.models.workflow_event import WorkflowEventDelivery, WorkflowEventTrigger
from app.core.logging import request_id_var


async def process_event_delivery(
    db: AsyncSession,
    *,
    delivery_id: uuid.UUID,
) -> WorkflowEventDelivery:
    """Convert a received event delivery into exactly one workflow execution."""

    result = await db.execute(
        select(WorkflowEventDelivery)
        .where(WorkflowEventDelivery.id == delivery_id)
        .with_for_update()
    )
    delivery = result.scalar_one_or_none()
    if delivery is None:
        raise NotFoundError("Workflow event delivery not found")

    if delivery.workflow_run_id is not None:
        return delivery

    trigger_result = await db.execute(
        select(WorkflowEventTrigger).where(
            WorkflowEventTrigger.id == delivery.trigger_id
        )
    )
    trigger = trigger_result.scalar_one_or_none()

    if trigger is None or not trigger.is_active:
        delivery.status = "rejected"
        delivery.error = {"code": "TRIGGER_UNAVAILABLE"}
        await db.flush()
        return delivery

    if delivery.status == "dispatched":
        return delivery

    idempotency_key = f"event:{trigger.id}:{delivery.event_id}"

    run = await workflow_service.create_workflow_run(
        db,
        tenant_id=delivery.tenant_id,
        workflow_id=trigger.workflow_id,
        input_data={
            "event": delivery.payload,
            "event_id": delivery.event_id,
            "event_type": delivery.event_type,
        },
        created_by=trigger.created_by,
        idempotency_key=idempotency_key,
    )

    delivery.workflow_run_id = run.id
    delivery.status = "dispatched"
    delivery.processed_at = datetime.now(timezone.utc)

    await outbox_service.enqueue(
        db,
        kind="workflow.execute",
        tenant_id=delivery.tenant_id,
        payload={"workflow_run_id": str(run.id)},
        dedupe_key=f"workflow.execute:{run.id}:event",
    )

    await audit_service.record(
        db,
        action="workflow.event.processed",
        actor_type="system",
        tenant_id=delivery.tenant_id,
        resource_type="workflow_event_delivery",
        resource_id=delivery.id,
        request_id=request_id_var.get(),
        metadata={"workflow_run_id": str(run.id), "event_id": delivery.event_id},
    )

    return delivery
