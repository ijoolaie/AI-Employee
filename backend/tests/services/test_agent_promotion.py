from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest

from app.models.agent_template import AgentTemplateStatus
from app.services.agent_promotion import promote_agent_template


@pytest.mark.asyncio
async def test_promotion_requires_independent_requester_and_approver():
    db = AsyncMock()
    user_id = uuid.uuid4()

    with pytest.raises(ValueError, match="independent"):
        await promote_agent_template(
            db,
            tenant_id=uuid.uuid4(),
            template_id=uuid.uuid4(),
            requested_by_user_id=user_id,
            approved_by_user_id=user_id,
        )
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_promotion_requires_comparable_evidence(monkeypatch):
    import app.services.agent_promotion as service

    db = AsyncMock()
    monkeypatch.setattr(service, "agent_promotion_evidence_summary", AsyncMock(return_value=[]))

    with pytest.raises(Exception, match="evidence is unavailable"):
        await promote_agent_template(
            db,
            tenant_id=uuid.uuid4(),
            template_id=uuid.uuid4(),
            requested_by_user_id=uuid.uuid4(),
            approved_by_user_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_promotion_reuses_governed_evaluation_and_publish(monkeypatch):
    import app.services.agent_promotion as service

    db = AsyncMock()
    template_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    requester = uuid.uuid4()
    approver = uuid.uuid4()
    candidate = SimpleNamespace(
        candidate_agent_template_id=template_id,
        comparable=True,
    )
    template = SimpleNamespace(status=AgentTemplateStatus.EVALUATING)
    publish_result = SimpleNamespace(id=template_id)

    monkeypatch.setattr(service, "agent_promotion_evidence_summary", AsyncMock(return_value=[candidate]))
    monkeypatch.setattr(service, "_load_template", AsyncMock(return_value=template))
    evaluation_gate = AsyncMock()
    monkeypatch.setattr(service, "assert_publishable_with_evidence", evaluation_gate)
    publish = AsyncMock(return_value=publish_result)
    monkeypatch.setattr(service, "publish_template", publish)

    result = await promote_agent_template(
        db,
        tenant_id=tenant_id,
        template_id=template_id,
        requested_by_user_id=requester,
        approved_by_user_id=approver,
    )

    assert result is publish_result
    evaluation_gate.assert_awaited_once_with(db, tenant_id=tenant_id, template_id=template_id)
    publish.assert_awaited_once_with(
        db,
        tenant_id=tenant_id,
        template_id=template_id,
        approved_by_user_id=approver,
    )
