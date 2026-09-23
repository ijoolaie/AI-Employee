import uuid

import pytest

from app.models.agent_workforce_proposal import AgentWorkforceProposalKind
from app.services import agent_workforce_proposal_service as proposal_service


@pytest.mark.asyncio
async def test_manager_proposal_requires_delegation(monkeypatch):
    async def deny(*args, **kwargs):
        raise ValueError("No active CEO delegation authorizes this manager operation")

    monkeypatch.setattr(proposal_service, "assert_operation_delegated", deny)

    with pytest.raises(ValueError, match="No active CEO delegation"):
        await proposal_service.create_manager_proposal(
            object(),
            tenant_id=uuid.uuid4(),
            manager_agent_instance_id=uuid.uuid4(),
            operation="staffing_proposal",
            sponsor_user_id=uuid.uuid4(),
            title="Add developer",
            rationale="Capacity gap",
            requested_name="AI Developer",
        )


@pytest.mark.asyncio
async def test_manager_proposal_persists_attribution_and_delegation(monkeypatch):
    delegation_id = uuid.uuid4()
    manager_id = uuid.uuid4()
    delegated_by = uuid.uuid4()
    sponsor = uuid.uuid4()
    target_employee_id = uuid.uuid4()
    captured = {}

    class Delegation:
        id = delegation_id
        delegated_by_user_id = delegated_by

    async def allow(*args, **kwargs):
        captured["operation"] = kwargs["operation"]
        return Delegation()

    async def create(*args, **kwargs):
        captured["requester_user_id"] = kwargs["requester_user_id"]
        return type(
            "Proposal",
            (),
            {
                "id": uuid.uuid4(),
                "kind": AgentWorkforceProposalKind.STAFFING,
                "source_type": "human",
                "proposed_by_agent_instance_id": None,
                "delegation_id": None,
                "manager_operation": None,
                "configuration": kwargs["configuration"],
            },
        )()

    async def record(*args, **kwargs):
        return None

    monkeypatch.setattr(proposal_service, "assert_operation_delegated", allow)
    monkeypatch.setattr(proposal_service, "create_proposal", create)
    monkeypatch.setattr(proposal_service, "record", record)

    class DB:
        async def flush(self):
            return None

    proposal = await proposal_service.create_manager_proposal(
        DB(),
        tenant_id=uuid.uuid4(),
        manager_agent_instance_id=manager_id,
        operation="replacement_proposal",
        sponsor_user_id=sponsor,
        title="Replace worker",
        rationale="Capacity recovery",
        requested_name="Replacement Worker",
        affected_employee_id=target_employee_id,
    )

    assert captured["operation"] == "replacement_proposal"
    assert captured["requester_user_id"] == delegated_by
    assert proposal.source_type == "internal_manager"
    assert proposal.proposed_by_agent_instance_id == manager_id
    assert proposal.delegation_id == delegation_id
    assert proposal.manager_operation == "replacement_proposal"
    assert proposal.kind is AgentWorkforceProposalKind.REPLACEMENT
    assert proposal.configuration["manager_operation_target_agent_instance_id"] == str(target_employee_id)


def test_manager_proposal_operations_are_explicit():
    allowed = {
        "staffing_proposal",
        "replacement_proposal",
        "transfer_proposal",
        "retirement_proposal",
    }
    assert allowed == {
        "staffing_proposal",
        "replacement_proposal",
        "transfer_proposal",
        "retirement_proposal",
    }
