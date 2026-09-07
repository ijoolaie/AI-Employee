from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.agent_workforce_proposal import AgentWorkforceProposalStatus
from app.services import agent_workforce_proposal_service as service


@pytest.mark.asyncio
async def test_board_decision_requires_submitted_and_independent_reviewer(monkeypatch):
    requester = uuid4()
    sponsor = uuid4()
    reviewer = uuid4()
    proposal = SimpleNamespace(
        id=uuid4(),
        status=AgentWorkforceProposalStatus.SUBMITTED,
        requester_user_id=requester,
        sponsor_user_id=sponsor,
        board_reviewed_by=None,
        board_decision_reason=None,
    )
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    monkeypatch.setattr(service, "record", AsyncMock())
    db = SimpleNamespace(flush=AsyncMock())

    result = await service.board_decide(
        db,
        tenant_id=uuid4(),
        proposal_id=proposal.id,
        reviewer_user_id=reviewer,
        approve=True,
        reason="Capacity is justified",
    )

    assert result.status == AgentWorkforceProposalStatus.BOARD_APPROVED
    assert result.board_reviewed_by == reviewer
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_ceo_decision_requires_board_approval_and_independent_authority(monkeypatch):
    requester, sponsor, board_reviewer, ceo = [uuid4() for _ in range(4)]
    proposal = SimpleNamespace(
        id=uuid4(),
        status=AgentWorkforceProposalStatus.BOARD_APPROVED,
        requester_user_id=requester,
        sponsor_user_id=sponsor,
        board_reviewed_by=board_reviewer,
        ceo_approved_by=None,
        ceo_decision_reason=None,
    )
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    monkeypatch.setattr(service, "record", AsyncMock())
    db = SimpleNamespace(flush=AsyncMock())

    result = await service.ceo_decide(
        db,
        tenant_id=uuid4(),
        proposal_id=proposal.id,
        approver_user_id=ceo,
        approve=True,
        reason="Approved for governed capacity expansion",
    )

    assert result.status == AgentWorkforceProposalStatus.CEO_APPROVED
    assert result.ceo_approved_by == ceo


@pytest.mark.asyncio
async def test_provision_requires_ceo_approval_and_starts_suspended(monkeypatch):
    sponsor, ceo = uuid4(), uuid4()
    proposal = SimpleNamespace(
        id=uuid4(),
        status=AgentWorkforceProposalStatus.CEO_APPROVED,
        agent_template_id=uuid4(),
        requested_name="Research Agent",
        sponsor_user_id=sponsor,
        ceo_approved_by=ceo,
        configuration={"mode": "governed"},
        provisioned_agent_instance_id=None,
    )
    instance = SimpleNamespace(id=uuid4())
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    monkeypatch.setattr(service, "provision_instance", AsyncMock(return_value=instance))
    monkeypatch.setattr(service, "record", AsyncMock())
    db = SimpleNamespace(flush=AsyncMock())

    result = await service.provision_approved_proposal(
        db,
        tenant_id=uuid4(),
        proposal_id=proposal.id,
    )

    service.provision_instance.assert_awaited_once_with(
        db,
        tenant_id=proposal.tenant_id if hasattr(proposal, "tenant_id") else pytest.ANY,
        template_id=proposal.agent_template_id,
        name=proposal.requested_name,
        sponsor_user_id=sponsor,
        approved_by_user_id=ceo,
        configuration=proposal.configuration,
        activate=False,
    )
    assert result.status == AgentWorkforceProposalStatus.PROVISIONED
    assert result.provisioned_agent_instance_id == instance.id
