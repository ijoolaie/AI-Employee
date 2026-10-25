"""PostgreSQL-backed acceptance for the governed WhatsApp outbound path.

The provider adapter is mocked: this test verifies durable approval/outbox/worker
coordination without sending a real WhatsApp message.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.core.exceptions import ValidationAppError
from app.models.customer_channel import CustomerChannel
from app.models.employee import Employee, EmployeeVersion
from app.models.outbox import OutboxMessage
from app.models.run import Run
from app.models.tenant import Tenant
from app.models.tool_approval import ToolApprovalRequest
from app.workers import whatsapp_worker


@pytest.mark.asyncio
async def test_postgres_persists_exact_call_approval_and_worker_dispatches_once(monkeypatch):
    tenant_id, employee_id, version_id, run_id = (uuid4() for _ in range(4))
    channel_id, approval_id, outbox_id, agent_id = (uuid4() for _ in range(4))
    tool_call_id = f"call_{uuid4().hex}"
    slug = f"wa-approval-{uuid4().hex[:16]}"
    recipient = "+15551234567"
    text = "PostgreSQL-backed approval acceptance"
    arguments = {"channel_id": str(channel_id), "recipient": recipient, "text": text}

    async with AsyncSessionLocal() as db:
        tenant = Tenant(id=tenant_id, name="WhatsApp Approval Test", slug=slug, status="active")
        db.add(tenant)
        await db.flush()

        employee = Employee(
            id=employee_id,
            tenant_id=tenant_id,
            slug=f"wa-employee-{uuid4().hex[:8]}",
            name="WhatsApp Approval Test Employee",
            kind="custom",
            is_active=True,
        )
        db.add(employee)
        await db.flush()

        version = EmployeeVersion(
            id=version_id,
            employee_id=employee_id,
            version_number=1,
            is_current=True,
            input_schema={},
            output_schema={},
            prompt_template="",
            allowed_tools=["whatsapp.send_text"],
            rules={},
        )
        db.add(version)
        await db.flush()

        run = Run(
            id=run_id,
            tenant_id=tenant_id,
            employee_id=employee_id,
            employee_version_id=version_id,
            status="pending",
            input_data={},
        )
        channel = CustomerChannel(
            id=channel_id,
            tenant_id=tenant_id,
            employee_id=employee_id,
            name="WhatsApp Approval Test Channel",
            channel_type="whatsapp",
            public_key=f"pk_{uuid4().hex}",
            config={},
            is_active=True,
        )
        approval = ToolApprovalRequest(
            id=approval_id,
            tenant_id=tenant_id,
            run_id=run_id,
            tool_name="whatsapp.send_text",
            tool_call_id=tool_call_id,
            arguments=arguments,
            continuation_messages=[],
            iteration=0,
            status="consumed",
        )
        proof = {
            "tenant_id": str(tenant_id),
            "agent_instance_id": str(agent_id),
            "run_id": str(run_id),
            "tool_name": "whatsapp.send_text",
        }
        payload = {
            **arguments,
            "run_id": str(run_id),
            "tool_name": "whatsapp.send_text",
            "tool_call_id": tool_call_id,
            "approval_request_id": str(approval_id),
            "_agent_governance": proof,
        }
        outbox = OutboxMessage(
            id=outbox_id,
            tenant_id=tenant_id,
            kind="whatsapp.send_text",
            dedupe_key=f"whatsapp:{run_id}:{tool_call_id}",
            payload=payload,
            status="processing",
            attempts=1,
        )
        db.add_all([run, channel, approval, outbox])
        await db.commit()

    async def allow_policy(_db, _request):
        return None

    @asynccontextmanager
    async def test_worker_session():
        async with AsyncSessionLocal() as session:
            yield session

    provider_calls = []

    async def fake_deliver_text(**kwargs):
        provider_calls.append(kwargs)
        return SimpleNamespace(provider_message_id="mock-wamid-acceptance", status="accepted")

    monkeypatch.setattr(whatsapp_worker, "assert_authorized", allow_policy)
    monkeypatch.setattr(whatsapp_worker, "worker_db_session", test_worker_session)
    monkeypatch.setattr(whatsapp_worker, "deliver_text", fake_deliver_text)

    # A separate session proves the approval is durable and exact-call-bound.
    async with AsyncSessionLocal() as db:
        persisted_approval = await db.get(ToolApprovalRequest, approval_id)
        persisted_outbox = await db.get(OutboxMessage, outbox_id)
        assert persisted_approval is not None
        assert persisted_approval.status == "consumed"
        assert persisted_approval.arguments == arguments
        assert persisted_outbox is not None
        assert persisted_outbox.payload["tool_call_id"] == tool_call_id

        # A foreign/missing approval ID must not authorize this tenant's outbox.
        tampered = OutboxMessage(
            id=uuid4(),
            tenant_id=tenant_id,
            kind="whatsapp.send_text",
            payload={
                **payload,
                "approval_request_id": str(uuid4()),
            },
            status="processing",
            attempts=1,
        )
        with pytest.raises(
            ValidationAppError,
            match="does not match its consumed exact-call approval",
        ):
            await whatsapp_worker._validate_and_load(db, tampered)

    # The real worker path runs its DB validations and status transitions, while
    # the provider boundary is a local stub and cannot send an external message.
    await whatsapp_worker._send(str(outbox_id))

    async with AsyncSessionLocal() as db:
        final_outbox = await db.get(OutboxMessage, outbox_id)
        assert final_outbox is not None
        assert final_outbox.status == "dispatched"
        assert final_outbox.payload["provider_message_id"] == "mock-wamid-acceptance"
        assert final_outbox.payload["provider_status"] == "accepted"
        assert await db.scalar(
            select(ToolApprovalRequest.id).where(
                ToolApprovalRequest.id == approval_id,
                ToolApprovalRequest.tenant_id == tenant_id,
                ToolApprovalRequest.run_id == run_id,
                ToolApprovalRequest.tool_call_id == tool_call_id,
                ToolApprovalRequest.status == "consumed",
            )
        ) == approval_id

    assert len(provider_calls) == 1
    assert provider_calls[0]["tenant_id"] == tenant_id
    assert provider_calls[0]["channel_type"] == "whatsapp"
    assert provider_calls[0]["recipient"] == recipient
    assert provider_calls[0]["text"] == text

    # Remove only this test's mutable rows. The test uses a unique tenant slug.
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OutboxMessage).where(OutboxMessage.id == outbox_id))
        await db.execute(delete(ToolApprovalRequest).where(ToolApprovalRequest.id == approval_id))
        await db.execute(delete(Run).where(Run.id == run_id))
        await db.execute(delete(CustomerChannel).where(CustomerChannel.id == channel_id))
        await db.execute(delete(EmployeeVersion).where(EmployeeVersion.id == version_id))
        await db.execute(delete(Employee).where(Employee.id == employee_id))
        await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await db.commit()
