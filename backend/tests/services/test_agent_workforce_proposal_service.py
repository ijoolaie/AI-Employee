from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.models.agent_workforce_proposal import AgentWorkforceProposalStatus
from app.services import agent_workforce_proposal_service as service


@pytest.mark.asyncio
async def test_board_decision_requires_submitted_and_independent_reviewer(monkeypatch):
    requester, sponsor, reviewer = uuid4(), uuid4(), uuid4()
    proposal = SimpleNamespace(id=uuid4(), status=AgentWorkforceProposalStatus.SUBMITTED, requester_user_id=requester, sponsor_user_id=sponsor, board_reviewed_by=None, board_decision_reason=None)
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    monkeypatch.setattr(service, "record", AsyncMock())
    db = SimpleNamespace(flush=AsyncMock())
    result = await service.board_decide(db, tenant_id=uuid4(), proposal_id=proposal.id, reviewer_user_id=reviewer, approve=True, reason="Capacity is justified")
    assert result.status == AgentWorkforceProposalStatus.BOARD_APPROVED
    assert result.board_reviewed_by == reviewer
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_ceo_decision_requires_board_approval_and_independent_authority(monkeypatch):
    requester, sponsor, board_reviewer, ceo = [uuid4() for _ in range(4)]
    proposal = SimpleNamespace(id=uuid4(), status=AgentWorkforceProposalStatus.BOARD_APPROVED, requester_user_id=requester, sponsor_user_id=sponsor, board_reviewed_by=board_reviewer, ceo_approved_by=None, ceo_decision_reason=None)
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    monkeypatch.setattr(service, "record", AsyncMock())
    db = SimpleNamespace(flush=AsyncMock())
    result = await service.ceo_decide(db, tenant_id=uuid4(), proposal_id=proposal.id, approver_user_id=ceo, approve=True, reason="Approved")
    assert result.status == AgentWorkforceProposalStatus.CEO_APPROVED
    assert result.ceo_approved_by == ceo


@pytest.mark.asyncio
async def test_provision_requires_ceo_approval_and_starts_suspended(monkeypatch):
    tenant_id, sponsor, ceo = uuid4(), uuid4(), uuid4()
    proposal = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, status=AgentWorkforceProposalStatus.CEO_APPROVED, agent_template_id=uuid4(), requested_name="Research Agent", sponsor_user_id=sponsor, ceo_approved_by=ceo, configuration={"mode": "governed"}, provisioned_agent_instance_id=None)
    instance = SimpleNamespace(id=uuid4())
    provision = AsyncMock(return_value=instance)
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    monkeypatch.setattr(service, "provision_instance", provision)
    monkeypatch.setattr(service, "record", AsyncMock())
    db = SimpleNamespace(flush=AsyncMock())
    result = await service.provision_approved_proposal(db, tenant_id=tenant_id, proposal_id=proposal.id)
    provision.assert_awaited_once_with(db, tenant_id=tenant_id, template_id=proposal.agent_template_id, name=proposal.requested_name, sponsor_user_id=sponsor, approved_by_user_id=ceo, configuration=proposal.configuration, activate=False)
    assert result.status == AgentWorkforceProposalStatus.PROVISIONED
    assert result.provisioned_agent_instance_id == instance.id


@pytest.mark.asyncio
async def test_activation_requires_approved_access_review_and_independent_activator(monkeypatch):
    tenant_id = uuid4()
    requester, sponsor, board, ceo, activator = [uuid4() for _ in range(5)]
    proposal = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, status=AgentWorkforceProposalStatus.PROVISIONED, provisioned_agent_instance_id=uuid4(), requester_user_id=requester, sponsor_user_id=sponsor, board_reviewed_by=board, ceo_approved_by=ceo)
    instance = SimpleNamespace(status=AgentInstanceStatus.SUSPENDED, enabled=False)
    identity = SimpleNamespace(id=uuid4())
    review = SimpleNamespace(id=uuid4())

    class Result:
        def __init__(self, value): self.value = value
        def scalar_one_or_none(self): return self.value

    execute = AsyncMock(side_effect=[Result(proposal), Result(instance), Result(identity), Result(review)])
    db = SimpleNamespace(execute=execute, flush=AsyncMock())
    monkeypatch.setattr(service, "record", AsyncMock())
    result = await service.activate_provisioned_proposal(db, tenant_id=tenant_id, proposal_id=proposal.id, activated_by_user_id=activator)
    assert result is proposal
    assert instance.status == AgentInstanceStatus.ENABLED
    assert instance.enabled is True
    db.flush.assert_awaited_once()
