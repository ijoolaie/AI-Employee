from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError
from app.models.agent_access_review import AgentAccessReviewDecision
from app.models.agent_instance import AgentInstanceStatus
from app.services import agent_governance as service


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


@pytest.mark.asyncio
async def test_approved_access_review_cannot_reactivate_enabled_instance(monkeypatch):
    tenant_id = uuid4()
    identity = SimpleNamespace(
        id=uuid4(),
        agent_instance_id=uuid4(),
        owner_user_id=uuid4(),
        sponsor_user_id=uuid4(),
        active=False,
        revoked_at=uuid4(),
    )
    instance = SimpleNamespace(
        id=identity.agent_instance_id,
        tenant_id=tenant_id,
        status=AgentInstanceStatus.ENABLED,
    )
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[Result(identity), Result(instance)]),
        add=SimpleNamespace(),
        flush=AsyncMock(),
        refresh=AsyncMock(),
    )

    with pytest.raises(ConflictError, match="governed workforce activation"):
        await service.review_access(
            db,
            tenant_id=tenant_id,
            identity_id=identity.id,
            reviewer_user_id=uuid4(),
            decision=AgentAccessReviewDecision.APPROVED,
            next_review_at=None,
            reason="Renewed",
        )

    db.flush.assert_not_awaited()
    db.refresh.assert_not_awaited()
    assert identity.active is False


@pytest.mark.asyncio
async def test_approved_access_review_remains_valid_for_suspended_instance(monkeypatch):
    tenant_id = uuid4()
    identity = SimpleNamespace(
        id=uuid4(),
        agent_instance_id=uuid4(),
        owner_user_id=uuid4(),
        sponsor_user_id=uuid4(),
        active=False,
        revoked_at=uuid4(),
    )
    instance = SimpleNamespace(
        id=identity.agent_instance_id,
        tenant_id=tenant_id,
        status=AgentInstanceStatus.SUSPENDED,
    )
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[Result(identity), Result(instance)]),
        add=lambda review: setattr(db, "review", review),
        flush=AsyncMock(),
        refresh=AsyncMock(),
    )

    result = await service.review_access(
        db,
        tenant_id=tenant_id,
        identity_id=identity.id,
        reviewer_user_id=uuid4(),
        decision=AgentAccessReviewDecision.APPROVED,
        next_review_at=None,
        reason="Initial approval",
    )

    assert result.decision == AgentAccessReviewDecision.APPROVED
    assert identity.active is True
    assert identity.revoked_at is None
    db.flush.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)
