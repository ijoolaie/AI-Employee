from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.edition_control import (
    list_reseller_support_escalations,
    list_vendor_support_escalations,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint,tenant_kind",
    [
        (list_vendor_support_escalations, "vendor"),
        (list_reseller_support_escalations, "reseller"),
    ],
)
async def test_support_inbox_lists_only_escalations_addressed_to_current_tenant(endpoint, tenant_kind):
    tenant_id = uuid4()
    source_tenant_id = uuid4()
    ticket = SimpleNamespace(
        id=uuid4(),
        from_tenant_id=source_tenant_id,
        to_tenant_id=tenant_id,
        status="open",
        subject="World room purchase question",
        description="Customer asks about a pending room purchase.",
    )
    result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [ticket]))
    db = AsyncMock()
    db.execute.return_value = result
    ctx = SimpleNamespace(tenant_id=tenant_id, tenant=SimpleNamespace(tenant_kind=tenant_kind))

    response = await endpoint(ctx, db)

    assert response.data[0].id == ticket.id
    assert response.data[0].to_tenant_id == tenant_id
    statement = str(db.execute.await_args.args[0])
    assert "support_escalations.to_tenant_id" in statement
    assert "support_escalations.created_at" in statement


from fastapi import HTTPException

from app.api.v1.edition_control import (
    update_reseller_support_escalation_status,
    update_vendor_support_escalation_status,
)
from app.schemas.edition import SupportEscalationStatusRequest
from app.services import edition_service


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint,tenant_kind",
    [
        (update_vendor_support_escalation_status, "vendor"),
        (update_reseller_support_escalation_status, "reseller"),
    ],
)
async def test_support_inbox_status_change_is_tenant_scoped_and_audited(endpoint, tenant_kind, monkeypatch):
    tenant_id = uuid4()
    actor_id = uuid4()
    ticket = SimpleNamespace(
        id=uuid4(),
        from_tenant_id=uuid4(),
        to_tenant_id=tenant_id,
        status="open",
        subject="Need help",
        description="A detailed support request.",
    )
    db = AsyncMock()
    db.execute.return_value.scalar_one_or_none.return_value = ticket
    audit = AsyncMock()
    monkeypatch.setattr(edition_service, "record_audit", audit)
    ctx = SimpleNamespace(tenant_id=tenant_id, user_id=actor_id, tenant=SimpleNamespace(tenant_kind=tenant_kind))

    response = await endpoint(ticket.id, SupportEscalationStatusRequest(status="in_progress"), ctx, db)

    assert response.data.status == "in_progress"
    assert ticket.status == "in_progress"
    statement = str(db.execute.await_args.args[0])
    assert "support_escalations.to_tenant_id" in statement
    audit.assert_awaited_once_with(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="support.escalation.status_changed",
        resource_type="support_escalation",
        resource_id=str(ticket.id),
        metadata={"from_status": "open", "to_status": "in_progress"},
    )


@pytest.mark.asyncio
async def test_support_inbox_cannot_update_escalation_for_another_tenant(monkeypatch):
    db = AsyncMock()
    db.execute.return_value.scalar_one_or_none.return_value = None
    ctx = SimpleNamespace(tenant_id=uuid4(), user_id=uuid4(), tenant=SimpleNamespace(tenant_kind="vendor"))
    with pytest.raises(HTTPException) as exc:
        await update_vendor_support_escalation_status(
            uuid4(), SupportEscalationStatusRequest(status="resolved"), ctx, db
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_support_inbox_rejects_invalid_status_transition(monkeypatch):
    tenant_id = uuid4()
    ticket = SimpleNamespace(
        id=uuid4(), from_tenant_id=uuid4(), to_tenant_id=tenant_id,
        status="resolved", subject="Need help", description="A detailed support request.",
    )
    db = AsyncMock()
    db.execute.return_value.scalar_one_or_none.return_value = ticket
    audit = AsyncMock()
    monkeypatch.setattr(edition_service, "record_audit", audit)
    ctx = SimpleNamespace(tenant_id=tenant_id, user_id=uuid4(), tenant=SimpleNamespace(tenant_kind="vendor"))
    with pytest.raises(HTTPException) as exc:
        await update_vendor_support_escalation_status(
            ticket.id, SupportEscalationStatusRequest(status="in_progress"), ctx, db
        )
    assert exc.value.status_code == 409
    audit.assert_not_awaited()
