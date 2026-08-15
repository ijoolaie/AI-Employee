"""Authenticated trigger management plus public webhook ingestion."""
from __future__ import annotations
import json
import uuid
from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy import select
from app.models.workflow_event import WorkflowEventTrigger, WorkflowEventDelivery
from app.core.deps import DbSession, WorkflowEventWriteContext, WorkflowEventReadContext
from app.core.exceptions import ValidationAppError
from app.schemas.common import APIResponse
from app.schemas.workflow import WorkflowEventTriggerCreate, WorkflowEventTriggerCreatedResponse, WorkflowEventTriggerResponse, WorkflowEventTriggerRotatedResponse, WorkflowEventTriggerUpdate, WorkflowEventDeliveryResponse
from app.services import workflow_trigger_service
from app.core.config import get_settings

router = APIRouter(tags=["workflow-events"])

@router.post("/workflows/{workflow_id}/event-triggers", response_model=APIResponse[WorkflowEventTriggerCreatedResponse], status_code=status.HTTP_201_CREATED)
async def create_event_trigger(workflow_id: uuid.UUID, payload: WorkflowEventTriggerCreate, ctx: WorkflowEventWriteContext, db: DbSession):
    trigger, secret = await workflow_trigger_service.create_event_trigger(db, tenant_id=ctx.tenant_id, workflow_id=workflow_id, event_type=payload.event_type, created_by=ctx.user_id)
    data = WorkflowEventTriggerCreatedResponse.model_validate(trigger).model_copy(update={"webhook_secret": secret, "webhook_url": f"/api/v1/webhooks/workflows/{trigger.id}"})
    return APIResponse(success=True, data=data)

@router.get("/workflows/{workflow_id}/event-triggers", response_model=APIResponse[list[WorkflowEventTriggerResponse]])
async def list_event_triggers(workflow_id: uuid.UUID, ctx: WorkflowEventReadContext, db: DbSession):
    await workflow_trigger_service.get_workflow_for_trigger(db, workflow_id=workflow_id, tenant_id=ctx.tenant_id)
    rows = await db.execute(select(WorkflowEventTrigger).where(WorkflowEventTrigger.workflow_id == workflow_id, WorkflowEventTrigger.tenant_id == ctx.tenant_id))
    return APIResponse(success=True, data=[WorkflowEventTriggerResponse.model_validate(x) for x in rows.scalars().all()])

@router.patch("/workflows/{workflow_id}/event-triggers/{trigger_id}", response_model=APIResponse[WorkflowEventTriggerResponse])
async def update_event_trigger(workflow_id: uuid.UUID, trigger_id: uuid.UUID, payload: WorkflowEventTriggerUpdate, ctx: WorkflowEventWriteContext, db: DbSession):
    trigger = await workflow_trigger_service.get_trigger(db, trigger_id=trigger_id, tenant_id=ctx.tenant_id, active_only=False)
    if trigger.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Workflow event trigger not found")
    if payload.is_active is not None:
        trigger.is_active = payload.is_active
        await db.flush()
        from app.core.logging import request_id_var
        await workflow_trigger_service.audit_service.record(
            db, action="workflow.event_trigger.updated", actor_id=ctx.user_id, tenant_id=ctx.tenant_id,
            resource_type="workflow_event_trigger", resource_id=trigger.id, request_id=request_id_var.get(),
            metadata={"workflow_id": str(trigger.workflow_id), "active": trigger.is_active},
        )
    return APIResponse(success=True, data=WorkflowEventTriggerResponse.model_validate(trigger))

@router.get("/workflow-event-deliveries", response_model=APIResponse[list[WorkflowEventDeliveryResponse]])
async def list_workflow_event_deliveries(ctx: WorkflowEventReadContext, db: DbSession, trigger_id: uuid.UUID | None = None, status_filter: str | None = None):
    stmt = select(WorkflowEventDelivery).where(WorkflowEventDelivery.tenant_id == ctx.tenant_id).order_by(WorkflowEventDelivery.received_at.desc()).limit(200)
    if trigger_id is not None:
        stmt = stmt.where(WorkflowEventDelivery.trigger_id == trigger_id)
    if status_filter:
        stmt = stmt.where(WorkflowEventDelivery.status == status_filter)
    rows = await db.execute(stmt)
    return APIResponse(success=True, data=[WorkflowEventDeliveryResponse.model_validate(x) for x in rows.scalars().all()])

@router.post("/workflow-event-deliveries/{delivery_id}/replay", response_model=APIResponse[WorkflowEventDeliveryResponse])
async def replay_workflow_event_delivery(delivery_id: uuid.UUID, ctx: WorkflowEventWriteContext, db: DbSession):
    result = await db.execute(select(WorkflowEventDelivery).where(WorkflowEventDelivery.id == delivery_id, WorkflowEventDelivery.tenant_id == ctx.tenant_id).with_for_update())
    delivery = result.scalar_one_or_none()
    if delivery is None:
        raise HTTPException(status_code=404, detail="Workflow event delivery not found")
    trigger = await workflow_trigger_service.get_trigger(db, trigger_id=delivery.trigger_id, tenant_id=ctx.tenant_id, active_only=True)
    delivery.status = "accepted"
    delivery.workflow_run_id = None
    delivery.attempts = 0
    delivery.error = None
    delivery.processed_at = None
    await db.flush()
    from app.services.outbox_service import enqueue
    await enqueue(db, kind="workflow.event_dispatch", tenant_id=delivery.tenant_id, payload={"delivery_id": str(delivery.id)}, dedupe_key=f"workflow.event_dispatch.replay:{delivery.id}:{uuid.uuid4()}")
    from app.core.logging import request_id_var
    await workflow_trigger_service.audit_service.record(db, action="workflow.event_delivery.replayed", actor_id=ctx.user_id, tenant_id=ctx.tenant_id, resource_type="workflow_event_delivery", resource_id=delivery.id, request_id=request_id_var.get(), metadata={"trigger_id": str(trigger.id), "event_id": delivery.event_id})
    return APIResponse(success=True, data=WorkflowEventDeliveryResponse.model_validate(delivery))

@router.post("/workflows/{workflow_id}/event-triggers/{trigger_id}/rotate-secret", response_model=APIResponse[WorkflowEventTriggerRotatedResponse])
async def rotate_event_trigger_secret(workflow_id: uuid.UUID, trigger_id: uuid.UUID, ctx: WorkflowEventWriteContext, db: DbSession):
    trigger = await workflow_trigger_service.get_trigger(db, trigger_id=trigger_id, tenant_id=ctx.tenant_id, active_only=False)
    if trigger.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Workflow event trigger not found")
    trigger, secret = await workflow_trigger_service.rotate_event_trigger_secret(db, trigger_id=trigger.id, tenant_id=ctx.tenant_id, actor_id=ctx.user_id)
    data = WorkflowEventTriggerRotatedResponse.model_validate(trigger).model_copy(update={"webhook_secret": secret, "webhook_url": f"/api/v1/webhooks/workflows/{trigger.id}"})
    return APIResponse(success=True, data=data)

@router.post("/webhooks/workflows/{trigger_id}", status_code=status.HTTP_202_ACCEPTED)
async def receive_workflow_webhook(trigger_id: uuid.UUID, request: Request, db: DbSession, x_event_id: str | None = Header(default=None), x_event_type: str | None = Header(default=None), x_webhook_signature: str | None = Header(default=None), x_webhook_timestamp: str | None = Header(default=None)):
    trigger = await workflow_trigger_service.get_public_trigger(db, trigger_id=trigger_id)
    body = await request.body()
    if len(body) > get_settings().webhook_max_payload_bytes:
        raise HTTPException(status_code=413, detail="Webhook payload too large")
    if not workflow_trigger_service.verify_replay_timestamp(x_webhook_timestamp):
        raise HTTPException(status_code=401, detail="Invalid or expired webhook timestamp")
    if not x_event_id:
        raise HTTPException(status_code=400, detail="Missing X-Event-Id")
    if x_event_type != trigger.event_type:
        raise HTTPException(status_code=400, detail="Invalid X-Event-Type")
    signed_payload = (x_webhook_timestamp + ".").encode("utf-8") + body
    if not workflow_trigger_service.verify_signature(workflow_trigger_service.resolve_trigger_secret(trigger), signed_payload, x_webhook_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Webhook body must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook JSON body must be an object")
    delivery, created = await workflow_trigger_service.receive_event(db, trigger=trigger, event_id=x_event_id, event_type=x_event_type, payload=payload)
    if created:
        from app.services.outbox_service import enqueue
        await enqueue(db, kind="workflow.event_dispatch", tenant_id=trigger.tenant_id, payload={"delivery_id": str(delivery.id)}, dedupe_key=f"workflow.event_dispatch:{delivery.id}")
    return {"success": True, "data": {"delivery_id": str(delivery.id), "duplicate": not created, "status": delivery.status}}
