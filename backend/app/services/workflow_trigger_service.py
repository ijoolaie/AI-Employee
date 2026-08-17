"""Workflow conditions, schedules, event triggers and webhook dispatch."""
from __future__ import annotations
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.logging import request_id_var
from app.models.workflow import Workflow, WorkflowRun
from app.models.workflow_event import WorkflowEventTrigger, WorkflowEventDelivery
from app.services import audit_service, workflow_service
from app.services.workflow_conditions import evaluate_condition
from app.core.security import encrypt_secret, decrypt_secret
from app.core.config import get_settings


def _parse_field(field: str, minimum: int, maximum: int) -> set[int]:
    values: set[int] = set()
    for token in field.split(','):
        token = token.strip()
        if not token: continue
        if token == '*': values.update(range(minimum, maximum + 1)); continue
        if token.startswith('*/'):
            step = int(token[2:]); values.update(range(minimum, maximum + 1, step)); continue
        if '-' in token:
            a, b = map(int, token.split('-', 1)); values.update(range(a, b + 1)); continue
        values.add(int(token))
    if not values or min(values) < minimum or max(values) > maximum:
        raise ValueError("Cron field out of range")
    return values


def next_cron_time(expr: str, after: datetime) -> datetime:
    """Small dependency-free 5-field cron evaluator: minute hour dom month dow."""
    fields = expr.split()
    if len(fields) != 5: raise ValueError("Cron must have 5 fields")
    mins = _parse_field(fields[0], 0, 59); hours = _parse_field(fields[1], 0, 23)
    dom = _parse_field(fields[2], 1, 31); months = _parse_field(fields[3], 1, 12); dow = _parse_field(fields[4], 0, 6)
    candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(366 * 24 * 60):
        cron_dow = (candidate.weekday() + 1) % 7
        dom_match, dow_match = candidate.day in dom, cron_dow in dow
        if candidate.month in months and candidate.hour in hours and candidate.minute in mins and (dom_match or dow_match):
            return candidate
        candidate += timedelta(minutes=1)
    raise ValueError("Could not find next cron occurrence within one year")


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def resolve_trigger_secret(trigger: WorkflowEventTrigger) -> str:
    if trigger.webhook_secret_encrypted:
        try:
            return decrypt_secret(trigger.webhook_secret_encrypted)
        except Exception:
            raise ValidationAppError("Webhook secret cannot be decrypted")
    return trigger.webhook_secret

def verify_signature(secret: str, payload: bytes, signature: str | None) -> bool:
    if not signature or not signature.startswith("sha256="): return False
    provided = signature.split("=", 1)[1].strip()
    if not provided: return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided)


def make_signature_from_stored_hash(secret_hash: str, payload: bytes) -> str:
    return "sha256=" + hmac.new(secret_hash.encode(), payload, hashlib.sha256).hexdigest()


async def rotate_event_trigger_secret(db: AsyncSession, *, trigger_id: uuid.UUID, tenant_id: uuid.UUID, actor_id: uuid.UUID) -> tuple[WorkflowEventTrigger, str]:
    trigger = await get_trigger(db, trigger_id=trigger_id, tenant_id=tenant_id, active_only=False)
    secret = secrets.token_urlsafe(32)
    trigger.webhook_secret = ""
    trigger.webhook_secret_hash = hash_secret(secret)
    trigger.webhook_secret_encrypted = encrypt_secret(secret)
    trigger.secret_rotated_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_service.record(db, action="workflow.event_trigger.secret_rotated", actor_id=actor_id, tenant_id=tenant_id, resource_type="workflow_event_trigger", resource_id=trigger.id, request_id=request_id_var.get(), metadata={"workflow_id": str(trigger.workflow_id)})
    return trigger, secret

def verify_replay_timestamp(timestamp: str | None, *, now: datetime | None = None) -> bool:
    if not timestamp:
        return False
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    current = int((now or datetime.now(timezone.utc)).timestamp())
    return abs(current - ts) <= get_settings().webhook_replay_window_seconds

async def create_event_trigger(db: AsyncSession, *, tenant_id: uuid.UUID, workflow_id: uuid.UUID, event_type: str, created_by: uuid.UUID) -> tuple[WorkflowEventTrigger, str]:
    workflow = await workflow_service.get_workflow(db, workflow_id=workflow_id, tenant_id=tenant_id)
    secret = secrets.token_urlsafe(32)
    trigger = WorkflowEventTrigger(tenant_id=tenant_id, workflow_id=workflow.id, event_type=event_type, webhook_secret="", webhook_secret_hash=hash_secret(secret), webhook_secret_encrypted=encrypt_secret(secret), created_by=created_by)
    db.add(trigger); await db.flush()
    await audit_service.record(db, action="workflow.event_trigger.created", actor_id=created_by, tenant_id=tenant_id, resource_type="workflow_event_trigger", resource_id=trigger.id, request_id=request_id_var.get(), metadata={"workflow_id": str(workflow.id), "event_type": event_type})
    return trigger, secret


async def get_trigger(db: AsyncSession, *, trigger_id: uuid.UUID, tenant_id: uuid.UUID, active_only: bool = True) -> WorkflowEventTrigger:
    stmt = select(WorkflowEventTrigger).where(WorkflowEventTrigger.id == trigger_id, WorkflowEventTrigger.tenant_id == tenant_id)
    if active_only: stmt = stmt.where(WorkflowEventTrigger.is_active.is_(True))
    result = await db.execute(stmt); trigger = result.scalar_one_or_none()
    if trigger is None: raise NotFoundError("Workflow event trigger not found")
    return trigger


async def receive_event(db: AsyncSession, *, trigger: WorkflowEventTrigger, event_id: str, event_type: str, payload: dict[str, Any]) -> tuple[WorkflowEventDelivery, bool]:
    if event_type != trigger.event_type: raise ValidationAppError("Event type does not match trigger")
    existing = await db.execute(select(WorkflowEventDelivery).where(WorkflowEventDelivery.trigger_id == trigger.id, WorkflowEventDelivery.event_id == event_id))
    delivery = existing.scalar_one_or_none()
    if delivery is not None: return delivery, False
    delivery = WorkflowEventDelivery(tenant_id=trigger.tenant_id, trigger_id=trigger.id, event_id=event_id, event_type=event_type, payload=payload, status="accepted", attempts=0)
    db.add(delivery); await db.flush()
    return delivery, True


async def dispatch_event(db: AsyncSession, *, delivery_id: uuid.UUID) -> WorkflowEventDelivery:
    result = await db.execute(select(WorkflowEventDelivery).where(WorkflowEventDelivery.id == delivery_id))
    delivery = result.scalar_one_or_none()
    if delivery is None: raise NotFoundError("Workflow event delivery not found")
    if delivery.workflow_run_id is not None and delivery.status == "dispatched": return delivery
    trigger_result = await db.execute(select(WorkflowEventTrigger).where(WorkflowEventTrigger.id == delivery.trigger_id))
    trigger = trigger_result.scalar_one_or_none()
    if trigger is None or not trigger.is_active:
        delivery.status = "rejected"; delivery.error = {"message": "Trigger inactive or missing"}; await db.flush(); return delivery
    delivery.attempts += 1
    try:
        run = await workflow_service.create_workflow_run(db, tenant_id=delivery.tenant_id, workflow_id=trigger.workflow_id, input_data={"event": delivery.payload, "event_id": delivery.event_id, "event_type": delivery.event_type}, created_by=trigger.created_by)
        delivery.workflow_run_id = run.id
        delivery.status = "dispatched"
        delivery.processed_at = datetime.now(timezone.utc)
        await audit_service.record(db, action="workflow.event.dispatched", actor_type="system", tenant_id=delivery.tenant_id, resource_type="workflow_event_delivery", resource_id=delivery.id, status="success", request_id=request_id_var.get(), metadata={"workflow_run_id": str(run.id), "event_id": delivery.event_id})
    except Exception as exc:
        delivery.status = "failed"; delivery.error = {"message": str(exc)[:2000]}; delivery.processed_at = datetime.now(timezone.utc)
        raise
    return delivery

async def create_schedule(db: AsyncSession, *, tenant_id: uuid.UUID, workflow_id: uuid.UUID, cron_expression: str, timezone_name: str, created_by: uuid.UUID):
    from zoneinfo import ZoneInfo
    from app.models.workflow_schedule import WorkflowSchedule
    try: ZoneInfo(timezone_name)
    except Exception as exc: raise ValidationAppError(f"Invalid timezone: {timezone_name}") from exc
    now = datetime.now(ZoneInfo(timezone_name))
    try: next_local = next_cron_time(cron_expression, now)
    except Exception as exc: raise ValidationAppError(str(exc)) from exc
    existing = await db.execute(select(WorkflowSchedule).where(WorkflowSchedule.tenant_id == tenant_id, WorkflowSchedule.workflow_id == workflow_id, WorkflowSchedule.cron_expression == cron_expression, WorkflowSchedule.timezone == timezone_name))
    if existing.scalar_one_or_none(): raise ValidationAppError("Schedule already exists")
    schedule = WorkflowSchedule(tenant_id=tenant_id, workflow_id=workflow_id, cron_expression=cron_expression, timezone=timezone_name, next_run_at=next_local.astimezone(timezone.utc), created_by=created_by)
    db.add(schedule); await db.flush()
    await audit_service.record(db, action="workflow.schedule.created", actor_id=created_by, tenant_id=tenant_id, resource_type="workflow_schedule", resource_id=schedule.id, request_id=request_id_var.get(), metadata={"workflow_id": str(workflow_id), "cron": cron_expression, "timezone": timezone_name})
    return schedule

async def claim_due_schedules(db: AsyncSession, *, now: datetime, limit: int = 50):
    from app.models.workflow_schedule import WorkflowSchedule
    result = await db.execute(select(WorkflowSchedule).where(WorkflowSchedule.is_active.is_(True), WorkflowSchedule.next_run_at.is_not(None), WorkflowSchedule.next_run_at <= now).with_for_update(skip_locked=True).limit(limit))
    return list(result.scalars().all())

async def advance_schedule(db: AsyncSession, *, schedule, run: WorkflowRun, now: datetime):
    from zoneinfo import ZoneInfo
    local_now = now.astimezone(ZoneInfo(schedule.timezone))
    schedule.last_run_at = now
    schedule.last_workflow_run_id = run.id
    schedule.next_run_at = next_cron_time(schedule.cron_expression, local_now).astimezone(timezone.utc)
    await db.flush()


async def get_public_trigger(db: AsyncSession, *, trigger_id: uuid.UUID):
    result = await db.execute(select(WorkflowEventTrigger).where(WorkflowEventTrigger.id == trigger_id))
    trigger = result.scalar_one_or_none()
    if trigger is None or not trigger.is_active:
        raise NotFoundError("Workflow event trigger not found")
    return trigger

async def get_workflow_for_trigger(db: AsyncSession, *, workflow_id: uuid.UUID, tenant_id: uuid.UUID):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == tenant_id))
    workflow = result.scalar_one_or_none()
    if workflow is None: raise NotFoundError("Workflow not found")
    return workflow
