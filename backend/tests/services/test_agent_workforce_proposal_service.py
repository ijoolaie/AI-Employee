from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, ValidationAppError
from app.models.agent_instance import AgentInstanceStatus
from app.models.agent_workforce_proposal import AgentWorkforceProposalStatus
from app.services import agent_workforce_proposal_service as service
from app.services.agent_governance_freshness import FINGERPRINT_KEY, execution_authority_fingerprint


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


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
async def test_board_reviewer_cannot_be_requester_or_sponsor(monkeypatch):
    requester, sponsor = uuid4(), uuid4()
    proposal = SimpleNamespace(id=uuid4(), status=AgentWorkforceProposalStatus.SUBMITTED, requester_user_id=requester, sponsor_user_id=sponsor)
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    db = SimpleNamespace(flush=AsyncMock())
    with pytest.raises(ValidationAppError, match="independent"):
        await service.board_decide(db, tenant_id=uuid4(), proposal_id=proposal.id, reviewer_user_id=sponsor, approve=True)
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_ceo_decision_records_freshness_proof(monkeypatch):
    tenant_id = uuid4()
    requester, sponsor, board_reviewer, ceo = [uuid4() for _ in range(4)]
    template_id, definition_id = uuid4(), uuid4()
    proposal = SimpleNamespace(
        id=uuid4(), status=AgentWorkforceProposalStatus.BOARD_APPROVED,
        requester_user_id=requester, sponsor_user_id=sponsor, board_reviewed_by=board_reviewer,
        ceo_approved_by=None, ceo_decision_reason=None, agent_template_id=template_id,
        agent_definition_id=definition_id, risk_tier=2, configuration={"mode": "governed", "max_concurrency": 2},
    )
    template = SimpleNamespace(
        id=template_id, status=SimpleNamespace(value="published"), agent_definition_id=definition_id,
        risk_tier=2, version=3, capability_contract={"read": True}, permission_policy={"scope": "ops"},
        approval_policy={"requires_ceo_approval": True}, install_policy={"requires_ceo_approval": True},
    )
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    monkeypatch.setattr(service, "record", AsyncMock())
    db = SimpleNamespace(execute=AsyncMock(return_value=Result(template)), flush=AsyncMock())
    result = await service.ceo_decide(db, tenant_id=tenant_id, proposal_id=proposal.id, approver_user_id=ceo, approve=True, reason="Approved")
    assert result.status == AgentWorkforceProposalStatus.CEO_APPROVED
    assert result.ceo_approved_by == ceo
    assert len(result.configuration[FINGERPRINT_KEY]) == 64


@pytest.mark.asyncio
async def test_ceo_approver_cannot_be_board_reviewer_or_sponsor(monkeypatch):
    requester, sponsor, board_reviewer = [uuid4() for _ in range(3)]
    proposal = SimpleNamespace(id=uuid4(), status=AgentWorkforceProposalStatus.BOARD_APPROVED, requester_user_id=requester, sponsor_user_id=sponsor, board_reviewed_by=board_reviewer)
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    db = SimpleNamespace(flush=AsyncMock())
    with pytest.raises(ValidationAppError, match="independent"):
        await service.ceo_decide(db, tenant_id=uuid4(), proposal_id=proposal.id, approver_user_id=board_reviewer, approve=True)
    db.flush.assert_not_awaited()


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
async def test_activation_requires_approved_access_review_and_fresh_decision(monkeypatch):
    tenant_id = uuid4()
    requester, sponsor, board, ceo, activator = [uuid4() for _ in range(5)]
    template_id, definition_id = uuid4(), uuid4()
    configuration = {"mode": "governed", "max_concurrency": 1, "budget_policy": {"monthly": 100}}
    template = SimpleNamespace(
        id=template_id, status=SimpleNamespace(value="published"), agent_definition_id=definition_id,
        version=1, risk_tier=2, capability_contract={"read": True}, permission_policy={"scope": "ops"},
        approval_policy={"requires_ceo_approval": True}, install_policy={"requires_ceo_approval": True},
    )
    fingerprint = execution_authority_fingerprint(
        tenant_id=tenant_id, template_id=template_id, template_version=1, agent_definition_id=definition_id,
        risk_tier=2, capability_contract=template.capability_contract, permission_policy=template.permission_policy,
        approval_policy=template.approval_policy, install_policy=template.install_policy,
        configuration=configuration, max_concurrency=1, budget_policy=configuration["budget_policy"],
    )
    proposal = SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, status=AgentWorkforceProposalStatus.PROVISIONED,
        provisioned_agent_instance_id=uuid4(), requester_user_id=requester, sponsor_user_id=sponsor,
        board_reviewed_by=board, ceo_approved_by=ceo,
        agent_template_id=template_id, agent_definition_id=definition_id, risk_tier=2,
        configuration={**configuration, FINGERPRINT_KEY: fingerprint},
    )
    instance = SimpleNamespace(id=proposal.provisioned_agent_instance_id, status=AgentInstanceStatus.SUSPENDED, enabled=False, max_concurrency=1, budget_policy=configuration["budget_policy"])
    identity = SimpleNamespace(id=uuid4())
    review = SimpleNamespace(id=uuid4())
    db = SimpleNamespace(execute=AsyncMock(side_effect=[Result(instance), Result(identity), Result(template), Result(review)]), flush=AsyncMock())
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    monkeypatch.setattr(service, "record", AsyncMock())

    result = await service.activate_provisioned_proposal(db, tenant_id=tenant_id, proposal_id=proposal.id, activated_by_user_id=activator)
    assert result is proposal
    assert instance.status == AgentInstanceStatus.ENABLED
    assert instance.enabled is True
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_activation_rejects_stale_template_change(monkeypatch):
    tenant_id = uuid4()
    requester, sponsor, board, ceo, activator = [uuid4() for _ in range(5)]
    template_id, definition_id = uuid4(), uuid4()
    approved_template = SimpleNamespace(
        id=template_id, version=1, agent_definition_id=definition_id, risk_tier=1,
        capability_contract={"read": True}, permission_policy={"scope": "ops"},
        approval_policy={}, install_policy={}, status=SimpleNamespace(value="published"),
    )
    approved_configuration = {"max_concurrency": 1, "budget_policy": {}}
    fingerprint = execution_authority_fingerprint(
        tenant_id=tenant_id, template_id=template_id, template_version=1, agent_definition_id=definition_id,
        risk_tier=1, capability_contract=approved_template.capability_contract,
        permission_policy=approved_template.permission_policy, approval_policy={}, install_policy={},
        configuration=approved_configuration, max_concurrency=1, budget_policy={},
    )
    stale_template = SimpleNamespace(**{**approved_template.__dict__, "capability_contract": {"write": True}})
    proposal = SimpleNamespace(
        id=uuid4(), status=AgentWorkforceProposalStatus.PROVISIONED, provisioned_agent_instance_id=uuid4(),
        requester_user_id=requester, sponsor_user_id=sponsor, board_reviewed_by=board, ceo_approved_by=ceo,
        agent_template_id=template_id, agent_definition_id=definition_id, risk_tier=1,
        configuration={**approved_configuration, FINGERPRINT_KEY: fingerprint},
    )
    instance = SimpleNamespace(id=proposal.provisioned_agent_instance_id, status=AgentInstanceStatus.SUSPENDED, enabled=False, max_concurrency=1, budget_policy={})
    identity = SimpleNamespace(id=uuid4())
    db = SimpleNamespace(execute=AsyncMock(side_effect=[Result(instance), Result(identity), Result(stale_template)]), flush=AsyncMock())
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    with pytest.raises(ConflictError, match="stale"):
        await service.activate_provisioned_proposal(db, tenant_id=tenant_id, proposal_id=proposal.id, activated_by_user_id=activator)
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_activation_activator_cannot_be_ceo_or_sponsor(monkeypatch):
    sponsor, ceo = uuid4(), uuid4()
    proposal = SimpleNamespace(id=uuid4(), status=AgentWorkforceProposalStatus.PROVISIONED, provisioned_agent_instance_id=uuid4(), requester_user_id=uuid4(), sponsor_user_id=sponsor, board_reviewed_by=uuid4(), ceo_approved_by=ceo)
    monkeypatch.setattr(service, "_get_locked", AsyncMock(return_value=proposal))
    db = SimpleNamespace(flush=AsyncMock())
    with pytest.raises(ValidationAppError, match="independent"):
        await service.activate_provisioned_proposal(db, tenant_id=uuid4(), proposal_id=proposal.id, activated_by_user_id=ceo)
    db.flush.assert_not_awaited()
