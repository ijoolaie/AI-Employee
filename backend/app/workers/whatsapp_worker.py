"""Approval-bound WhatsApp outbound worker.

A durable row enters an explicit `uncertain` state before the provider call.
Any exception after that boundary is not automatically retried because the
provider may already have accepted the message.
"""
from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select

from app.core.database import worker_db_session
from app.core.exceptions import ValidationAppError
from app.models.customer_channel import CustomerChannel
from app.models.outbox import OutboxMessage
from app.models.tool_approval import ToolApprovalRequest
from app.services.agent_policy_engine import PolicyRequest, assert_authorized
from app.services.channel_delivery import deliver_text
from app.services.outbox_service import mark_dispatched, mark_retry
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.whatsapp")


def _uuid(value: object, field: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValidationAppError(f"Malformed WhatsApp outbox {field}") from exc


async def _validate_and_load(db, row: OutboxMessage):
    payload = row.payload or {}
    proof = payload.get("_agent_governance")
    if not isinstance(proof, dict):
        raise ValidationAppError("WhatsApp outbox is missing Agent governance proof")
    tenant_id = _uuid(proof.get("tenant_id"), "tenant binding")
    agent_id = _uuid(proof.get("agent_instance_id"), "Agent binding")
    run_id = _uuid(payload.get("run_id"), "Run binding")
    proof_run_id = _uuid(proof.get("run_id"), "governance Run binding")
    approval_id = _uuid(payload.get("approval_request_id"), "approval binding")
    channel_id = _uuid(payload.get("channel_id"), "channel binding")
    tool_name = payload.get("tool_name")
    tool_call_id = payload.get("tool_call_id")
    delegation_id = _uuid(proof["delegation_id"], "delegation binding") if proof.get("delegation_id") else None

    if (
        row.tenant_id != tenant_id
        or run_id != proof_run_id
        or tool_name != "whatsapp.send_text"
        or proof.get("tool_name") != tool_name
        or not isinstance(tool_call_id, str)
        or not tool_call_id
        or not isinstance(payload.get("recipient"), str)
        or not isinstance(payload.get("text"), str)
    ):
        raise ValidationAppError("WhatsApp outbox governance binding mismatch")

    expected_arguments = {
        "channel_id": str(channel_id),
        "recipient": payload["recipient"],
        "text": payload["text"],
    }
    approval = (await db.execute(
        select(ToolApprovalRequest).where(
            ToolApprovalRequest.id == approval_id,
            ToolApprovalRequest.tenant_id == tenant_id,
            ToolApprovalRequest.run_id == run_id,
            ToolApprovalRequest.tool_name == tool_name,
            ToolApprovalRequest.tool_call_id == tool_call_id,
        ).with_for_update()
    )).scalar_one_or_none()
    # The approval is consumed by the synchronous registry boundary before
    # the outbox transaction commits. Pending/approved approvals cannot be
    # used as an alternate worker entry point.
    if approval is None or approval.status != "consumed" or approval.arguments != expected_arguments:
        raise ValidationAppError("WhatsApp outbox does not match its consumed exact-call approval")

    channel = (await db.execute(
        select(CustomerChannel).where(
            CustomerChannel.id == channel_id,
            CustomerChannel.tenant_id == tenant_id,
            CustomerChannel.channel_type == "whatsapp",
            CustomerChannel.is_active.is_(True),
        ).with_for_update()
    )).scalar_one_or_none()
    if channel is None:
        raise ValidationAppError("Active WhatsApp channel not found for this tenant")

    await assert_authorized(
        db,
        PolicyRequest(
            tenant_id=tenant_id,
            agent_instance_id=agent_id,
            action="tool.execute",
            tool_name=tool_name,
            required_permission="run.execute",
            run_id=run_id,
            delegation_id=delegation_id,
        ),
    )
    return tenant_id, channel, payload, approval, agent_id, run_id, delegation_id


async def _send(outbox_id: str) -> None:
    async with worker_db_session() as db:
        row = (await db.execute(
            select(OutboxMessage).where(OutboxMessage.id == _uuid(outbox_id, "row id")).with_for_update()
        )).scalar_one_or_none()
        if row is None or row.kind != "whatsapp.send_text" or row.status in {"dispatched", "dead", "uncertain"}:
            return
        if row.status not in {"processing", "pending"}:
            return

        side_effect_started = False
        try:
            tenant_id, channel, payload, _approval, _agent_id, _run_id, _delegation_id = await _validate_and_load(db, row)

            # The provider request cannot be made atomically with the DB. Commit
            # the uncertain fence first; crashes/timeouts after this point must
            # never be automatically retried as they could duplicate a message.
            row.status = "uncertain"
            await db.commit()
            side_effect_started = True

            # Recheck tenant ownership, channel state, and current Agent policy
            # immediately before the irreversible provider call.
            tenant_id, channel, payload, _approval, _agent_id, _run_id, _delegation_id = await _validate_and_load(db, row)
            delivery = await deliver_text(
                db=db,
                tenant_id=tenant_id,
                channel_type=channel.channel_type,
                channel_config=channel.config or {},
                recipient=payload["recipient"],
                text=payload["text"],
            )
            row.payload = {
                **(row.payload or {}),
                "provider_message_id": delivery.provider_message_id,
                "provider_status": delivery.status,
            }
            await mark_dispatched(db, row)
            await db.commit()
        except Exception as exc:
            await db.rollback()
            # Reload after rollback; never turn a provider-stage failure into a
            # retry. Only deterministic pre-provider failures are retryable.
            row = (await db.execute(
                select(OutboxMessage).where(OutboxMessage.id == _uuid(outbox_id, "row id")).with_for_update()
            )).scalar_one_or_none()
            if row is not None:
                if side_effect_started:
                    row.status = "uncertain"
                    row.last_error = f"{type(exc).__name__}: {exc}"[:4000]
                    await db.commit()
                    logger.error("WhatsApp outcome uncertain for outbox %s (%s)", outbox_id, type(exc).__name__)
                else:
                    await mark_retry(db, row, f"{type(exc).__name__}: {exc}", delay_seconds=min(300, 10 * max(1, row.attempts)))
                    await db.commit()
                    logger.warning("WhatsApp pre-send validation failed for outbox %s (%s)", outbox_id, type(exc).__name__)


@celery_app.task(name="whatsapp.send_text")
def send_whatsapp_text_task(outbox_id: str) -> None:
    asyncio.run(_send(outbox_id))
