from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.edition_control import (
    _create_support_escalation_message,
    _download_support_escalation_attachment,
    _list_outgoing_support_escalations,
    _list_support_escalation_messages,
)
from app.models.support_escalation_message import SupportEscalationMessage
from app.models.support_escalation_message_attachment import SupportEscalationMessageAttachment
from app.schemas.edition import SupportEscalationMessageRequest
from app.services import edition_service, storage


def _result(ticket=None, rows=None, pairs=None, values=None):
    if pairs is not None:
        return SimpleNamespace(all=lambda: pairs)
    if values is not None:
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: values))
    if rows is not None:
        return SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=lambda: rows),
            all=lambda: rows,
        )
    return SimpleNamespace(scalar_one_or_none=lambda: ticket, scalars=lambda: SimpleNamespace(all=lambda: []))


@pytest.mark.asyncio
async def test_reseller_sent_escalation_list_is_scoped_to_originating_tenant():
    tenant_id = uuid4()
    ticket = SimpleNamespace(
        id=uuid4(),
        from_tenant_id=tenant_id,
        to_tenant_id=uuid4(),
        opened_by=uuid4(),
        subject="Persistent support history",
        description="A reseller-created escalation",
        status="open",
        extra_data={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db = AsyncMock()
    db.execute.return_value = _result(values=[ticket])

    response = await _list_outgoing_support_escalations(db, tenant_id)

    assert [row.id for row in response.data] == [ticket.id]
    query = str(db.execute.await_args.args[0])
    assert "WHERE support_escalations.from_tenant_id =" in query
    assert "WHERE support_escalations.to_tenant_id =" not in query


@pytest.mark.asyncio
async def test_support_message_thread_is_scoped_to_ticket_participants():
    tenant_id = uuid4()
    ticket = SimpleNamespace(id=uuid4(), from_tenant_id=tenant_id, to_tenant_id=uuid4(), status="open")
    message = SimpleNamespace(
        id=uuid4(),
        escalation_id=ticket.id,
        author_tenant_id=tenant_id,
        author_user_id=uuid4(),
        body="We are looking into this.",
        created_at=datetime.now(timezone.utc),
    )
    db = AsyncMock()
    db.execute.side_effect = [_result(ticket), _result(rows=[message]), _result(pairs=[])]
    ctx = SimpleNamespace(tenant_id=tenant_id, user_id=message.author_user_id)

    response = await _list_support_escalation_messages(ticket.id, ctx, db)

    assert [row.id for row in response.data] == [message.id]
    ticket_query = str(db.execute.await_args_list[0].args[0])
    assert "support_escalations.from_tenant_id" in ticket_query
    assert "support_escalations.to_tenant_id" in ticket_query


@pytest.mark.asyncio
async def test_support_message_thread_hides_foreign_ticket():
    db = AsyncMock()
    db.execute.return_value = _result(ticket=None)
    ctx = SimpleNamespace(tenant_id=uuid4(), user_id=uuid4())

    with pytest.raises(HTTPException) as exc:
        await _list_support_escalation_messages(uuid4(), ctx, db)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_support_message_reply_is_audited_and_keeps_body_out_of_audit_metadata(monkeypatch):
    tenant_id = uuid4()
    actor_id = uuid4()
    ticket = SimpleNamespace(id=uuid4(), from_tenant_id=tenant_id, to_tenant_id=uuid4(), status="in_progress")
    db = AsyncMock()
    db.execute.return_value = _result(ticket=ticket)

    async def refresh(message):
        message.created_at = datetime.now(timezone.utc)

    db.refresh.side_effect = refresh
    audit = AsyncMock()
    monkeypatch.setattr(edition_service, "record_audit", audit)
    ctx = SimpleNamespace(tenant_id=tenant_id, user_id=actor_id)

    response = await _create_support_escalation_message(
        ticket.id,
        SupportEscalationMessageRequest(body="  Please share the next steps.  "),
        ctx,
        db,
    )

    assert response.data.body == "Please share the next steps."
    assert response.data.author_tenant_id == tenant_id
    audit.assert_awaited_once()
    assert audit.await_args.kwargs["action"] == "support.escalation.message_created"
    assert audit.await_args.kwargs["metadata"] == {"escalation_id": str(ticket.id)}
    assert "body" not in audit.await_args.kwargs["metadata"]


@pytest.mark.asyncio
async def test_support_message_rejects_attachment_not_owned_by_author_tenant(monkeypatch):
    tenant_id = uuid4()
    file_id = uuid4()
    ticket = SimpleNamespace(id=uuid4(), from_tenant_id=tenant_id, to_tenant_id=uuid4(), status="open")
    db = AsyncMock()
    db.execute.side_effect = [_result(ticket=ticket), _result(rows=[])]
    audit = AsyncMock()
    monkeypatch.setattr(edition_service, "record_audit", audit)
    ctx = SimpleNamespace(tenant_id=tenant_id, user_id=uuid4())

    with pytest.raises(HTTPException) as exc:
        await _create_support_escalation_message(
            ticket.id,
            SupportEscalationMessageRequest(body="Please review this file.", attachment_file_ids=[file_id]),
            ctx,
            db,
        )

    assert exc.value.status_code == 404
    db.add.assert_not_called()
    audit.assert_not_awaited()


@pytest.mark.asyncio
async def test_support_message_rejects_duplicate_attachment_ids():
    tenant_id = uuid4()
    ticket = SimpleNamespace(id=uuid4(), from_tenant_id=tenant_id, to_tenant_id=uuid4(), status="open")
    file_id = uuid4()
    db = AsyncMock()
    db.execute.return_value = _result(ticket=ticket)
    ctx = SimpleNamespace(tenant_id=tenant_id, user_id=uuid4())

    with pytest.raises(HTTPException) as exc:
        await _create_support_escalation_message(
            ticket.id,
            SupportEscalationMessageRequest(body="Duplicate file.", attachment_file_ids=[file_id, file_id]),
            ctx,
            db,
        )

    assert exc.value.status_code == 422
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_support_message_cannot_be_added_to_resolved_ticket(monkeypatch):
    tenant_id = uuid4()
    ticket = SimpleNamespace(id=uuid4(), from_tenant_id=tenant_id, to_tenant_id=uuid4(), status="resolved")
    db = AsyncMock()
    db.execute.return_value = _result(ticket=ticket)
    audit = AsyncMock()
    monkeypatch.setattr(edition_service, "record_audit", audit)
    ctx = SimpleNamespace(tenant_id=tenant_id, user_id=uuid4())

    with pytest.raises(HTTPException) as exc:
        await _create_support_escalation_message(
            ticket.id,
            SupportEscalationMessageRequest(body="Please reopen this."),
            ctx,
            db,
        )

    assert exc.value.status_code == 409
    db.add.assert_not_called()
    audit.assert_not_awaited()


@pytest.mark.asyncio
async def test_support_attachment_download_hides_nonparticipant_ticket(monkeypatch):
    db = AsyncMock()
    db.execute.return_value = _result(ticket=None)
    ctx = SimpleNamespace(tenant_id=uuid4(), user_id=uuid4())
    backend = SimpleNamespace(open=pytest.fail)
    monkeypatch.setattr(storage, "get_storage_backend", lambda: backend)

    with pytest.raises(HTTPException) as exc:
        await _download_support_escalation_attachment(uuid4(), uuid4(), ctx, db)

    assert exc.value.status_code == 404
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_support_attachment_download_rejects_attachment_from_another_ticket(monkeypatch):
    tenant_id = uuid4()
    ticket = SimpleNamespace(id=uuid4(), from_tenant_id=tenant_id, to_tenant_id=uuid4(), status="open")
    db = AsyncMock()
    db.execute.side_effect = [_result(ticket=ticket), SimpleNamespace(one_or_none=lambda: None)]
    ctx = SimpleNamespace(tenant_id=tenant_id, user_id=uuid4())
    backend = SimpleNamespace(open=pytest.fail)
    monkeypatch.setattr(storage, "get_storage_backend", lambda: backend)

    with pytest.raises(HTTPException) as exc:
        await _download_support_escalation_attachment(ticket.id, uuid4(), ctx, db)

    assert exc.value.status_code == 404
    assert db.execute.await_count == 2


def test_support_message_model_does_not_store_public_attachment_urls():
    fields = set(SupportEscalationMessage.__table__.columns.keys())
    assert {"id", "escalation_id", "author_tenant_id", "author_user_id", "body", "created_at"} <= fields
    assert "attachment_url" not in fields
    assert "status" not in fields


def test_support_attachment_model_prevents_reusing_one_file_across_messages():
    fields = set(SupportEscalationMessageAttachment.__table__.columns.keys())
    assert {"id", "message_id", "file_id", "created_at"} <= fields
    constraints = {constraint.name for constraint in SupportEscalationMessageAttachment.__table__.constraints}
    assert "uq_support_message_attachment_file" in constraints
