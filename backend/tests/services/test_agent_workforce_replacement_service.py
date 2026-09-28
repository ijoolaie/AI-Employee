from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.models.agent_instance import AgentInstanceStatus
from app.models.agent_workforce_proposal import AgentWorkforceProposalKind, AgentWorkforceProposalStatus
from app.services import agent_workforce_replacement_service as service


@pytest.mark.asyncio
async def test_prepare_replacement_cutover_validates_actor_tenant_before_mutation(monkeypatch):
    tenant_id = uuid4()
    proposal_id = uuid4()
    actor_user_id = uuid4()
    predecessor_id = uuid4()
    proposal = SimpleNamespace(
        id=proposal_id,
        kind=AgentWorkforceProposalKind.REPLACEMENT,
        status=AgentWorkforceProposalStatus.PROVISIONED,
        replacement_for_agent_instance_id=predecessor_id,
        requester_user_id=uuid4(),
        sponsor_user_id=uuid4(),
        board_reviewed_by=uuid4(),
        ceo_approved_by=uuid4(),
    )
    predecessor = SimpleNamespace(
        id=predecessor_id,
        status=AgentInstanceStatus.DRAINING,
        enabled=True,
    )

    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: predecessor)),
        flush=AsyncMock(),
    )
    locked = AsyncMock(return_value=proposal)
    validate_actor = AsyncMock()
    record = AsyncMock()
    monkeypatch.setattr(service, "_locked_proposal", locked)
    monkeypatch.setattr(service, "assert_users_belong_to_tenant", validate_actor)
    monkeypatch.setattr(service, "record", record)

    result = await service.prepare_replacement_cutover(
        db,
        tenant_id=tenant_id,
        proposal_id=proposal_id,
        requested_by_user_id=actor_user_id,
    )

    assert result is proposal
    validate_actor.assert_awaited_once_with(
        db,
        tenant_id=tenant_id,
        user_ids={actor_user_id},
        field_names={actor_user_id: "requested_by_user_id"},
    )
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_prepare_replacement_cutover_rejects_cross_tenant_actor_before_state_change(monkeypatch):
    tenant_id = uuid4()
    proposal_id = uuid4()
    actor_user_id = uuid4()
    proposal = SimpleNamespace(
        id=proposal_id,
        kind=AgentWorkforceProposalKind.REPLACEMENT,
        status=AgentWorkforceProposalStatus.PROVISIONED,
    )
    db = SimpleNamespace(execute=AsyncMock(), flush=AsyncMock())
    monkeypatch.setattr(service, "_locked_proposal", AsyncMock(return_value=proposal))
    monkeypatch.setattr(
        service,
        "assert_users_belong_to_tenant",
        AsyncMock(side_effect=ValidationAppError("requested_by_user_id must reference users belonging to the current tenant")),
    )

    with pytest.raises(ValidationAppError, match="requested_by_user_id"):
        await service.prepare_replacement_cutover(
            db,
            tenant_id=tenant_id,
            proposal_id=proposal_id,
            requested_by_user_id=actor_user_id,
        )

    db.execute.assert_not_awaited()
    db.flush.assert_not_awaited()
