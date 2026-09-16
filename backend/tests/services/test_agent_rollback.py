from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest

from app.core.exceptions import ConflictError, ValidationAppError
from app.models.agent_instance import AgentInstanceStatus
from app.models.agent_template import AgentTemplateStatus
from app.services.agent_rollback import create_rollback_proposal


@pytest.mark.asyncio
async def test_rollback_requires_independent_requester_and_sponsor():
    db = AsyncMock()
    user_id = uuid.uuid4()

    with pytest.raises(ValidationAppError, match="independently attributable"):
        await create_rollback_proposal(
            db,
            tenant_id=uuid.uuid4(),
            requester_user_id=user_id,
            sponsor_user_id=user_id,
            agent_instance_id=uuid.uuid4(),
            title="Rollback",
            rationale="Rollback after observed regression",
            requested_name="agent-rollback",
        )
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_rollback_requires_a_previously_published_version(monkeypatch):
    import app.services.agent_rollback as service

    db = AsyncMock()
    instance = SimpleNamespace(
        id=uuid.uuid4(),
        status=AgentInstanceStatus.ENABLED,
        agent_template_id=uuid.uuid4(),
    )
    current = SimpleNamespace(
        id=instance.agent_template_id,
        slug="sales-agent",
        agent_definition_id=uuid.uuid4(),
        version=3,
        status=AgentTemplateStatus.PUBLISHED,
    )
    results = [
        SimpleNamespace(scalar_one_or_none=lambda: instance),
        SimpleNamespace(scalar_one_or_none=lambda: current),
        SimpleNamespace(scalar_one_or_none=lambda: None),
    ]
    db.execute.side_effect = results

    with pytest.raises(ConflictError, match="previously published"):
        await create_rollback_proposal(
            db,
            tenant_id=uuid.uuid4(),
            requester_user_id=uuid.uuid4(),
            sponsor_user_id=uuid.uuid4(),
            agent_instance_id=instance.id,
            title="Rollback",
            rationale="Rollback after observed regression",
            requested_name="agent-rollback",
        )

    db.execute.assert_awaited()
    assert db.execute.await_count == 3
    assert service.create_replacement_proposal is not None


@pytest.mark.asyncio
async def test_rollback_targets_immediately_prior_version_and_reuses_replacement_governance(monkeypatch):
    import app.services.agent_rollback as service

    db = AsyncMock()
    tenant_id = uuid.uuid4()
    instance_id = uuid.uuid4()
    current_id = uuid.uuid4()
    previous_id = uuid.uuid4()
    instance = SimpleNamespace(
        id=instance_id,
        status=AgentInstanceStatus.ENABLED,
        agent_template_id=current_id,
    )
    current = SimpleNamespace(
        id=current_id,
        slug="sales-agent",
        agent_definition_id=uuid.uuid4(),
        version=4,
        status=AgentTemplateStatus.PUBLISHED,
    )
    previous = SimpleNamespace(
        id=previous_id,
        risk_tier=2,
        version=3,
        status=AgentTemplateStatus.PUBLISHED,
    )
    db.execute.side_effect = [
        SimpleNamespace(scalar_one_or_none=lambda: instance),
        SimpleNamespace(scalar_one_or_none=lambda: current),
        SimpleNamespace(scalar_one_or_none=lambda: previous),
    ]
    replacement = SimpleNamespace(id=uuid.uuid4())
    create_replacement = AsyncMock(return_value=replacement)
    monkeypatch.setattr(service, "create_replacement_proposal", create_replacement)

    result = await create_rollback_proposal(
        db,
        tenant_id=tenant_id,
        requester_user_id=uuid.uuid4(),
        sponsor_user_id=uuid.uuid4(),
        agent_instance_id=instance_id,
        title="Rollback sales agent",
        rationale="Observed regression",
        requested_name="sales-agent-rollback",
    )

    assert result is replacement
    create_replacement.assert_awaited_once()
    kwargs = create_replacement.await_args.kwargs
    assert kwargs["agent_template_id"] == previous_id
    assert kwargs["replacement_for_agent_instance_id"] == instance_id
    assert kwargs["risk_tier"] == 2
    assert kwargs["configuration"]["rollback"]["current_agent_template_version"] == 4
    assert kwargs["configuration"]["rollback"]["target_agent_template_version"] == 3
