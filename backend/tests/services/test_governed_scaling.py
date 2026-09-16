from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest

from app.core.exceptions import ValidationAppError
from app.services import governed_scaling


def _published_template():
    return SimpleNamespace(status=SimpleNamespace(value="published"), risk_tier=0)


@pytest.mark.asyncio
async def test_scaling_proposal_requires_independent_sponsor():
    with pytest.raises(ValidationAppError, match="independently attributable"):
        await governed_scaling.create_scaling_proposal(
            AsyncMock(),
            tenant_id=uuid.uuid4(),
            requester_user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            sponsor_user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            agent_template_id=uuid.uuid4(),
            requested_name_prefix="worker",
        )


@pytest.mark.asyncio
async def test_scaling_proposal_fails_closed_without_complete_evidence(monkeypatch):
    forecast = SimpleNamespace(
        evidence_complete=False,
        total_max_concurrency=4,
        projected_utilization=1.5,
        projected_required_concurrency=6,
        projected_backlog=2,
    )
    monkeypatch.setattr(governed_scaling, "capacity_forecast", AsyncMock(return_value=forecast))
    db = AsyncMock()
    db.execute.return_value.scalar_one_or_none.return_value = _published_template()

    with pytest.raises(ValidationAppError, match="complete capacity evidence"):
        await governed_scaling.create_scaling_proposal(
            db,
            tenant_id=uuid.uuid4(),
            requester_user_id=uuid.uuid4(),
            sponsor_user_id=uuid.uuid4(),
            agent_template_id=uuid.uuid4(),
            requested_name_prefix="worker",
        )


@pytest.mark.asyncio
async def test_scaling_proposal_creates_existing_governed_workforce_proposal(monkeypatch):
    forecast = SimpleNamespace(
        evidence_complete=True,
        total_max_concurrency=4,
        projected_utilization=1.5,
        projected_required_concurrency=6.1,
        projected_backlog=2,
    )
    create = AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4()))
    monkeypatch.setattr(governed_scaling, "capacity_forecast", AsyncMock(return_value=forecast))
    monkeypatch.setattr(governed_scaling, "create_proposal", create)

    db = AsyncMock()
    db.execute.return_value.scalar_one_or_none.return_value = _published_template()
    proposal, returned_forecast = await governed_scaling.create_scaling_proposal(
        db,
        tenant_id=uuid.uuid4(),
        requester_user_id=uuid.uuid4(),
        sponsor_user_id=uuid.uuid4(),
        agent_template_id=uuid.uuid4(),
        requested_name_prefix="worker",
        max_additional_concurrency=2,
    )

    assert proposal.id
    assert returned_forecast is forecast
    create.assert_awaited_once()
    kwargs = create.await_args.kwargs
    assert kwargs["risk_tier"] == 0
    assert kwargs["configuration"]["max_concurrency"] == 2
    assert kwargs["configuration"]["scaling_control"]["additional_concurrency_requested"] == 2
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_scaling_proposal_rejects_non_overloaded_capacity(monkeypatch):
    forecast = SimpleNamespace(
        evidence_complete=True,
        total_max_concurrency=4,
        projected_utilization=1.0,
        projected_required_concurrency=4,
        projected_backlog=0,
    )
    monkeypatch.setattr(governed_scaling, "capacity_forecast", AsyncMock(return_value=forecast))
    db = AsyncMock()
    db.execute.return_value.scalar_one_or_none.return_value = _published_template()

    with pytest.raises(ValidationAppError, match="scaling need"):
        await governed_scaling.create_scaling_proposal(
            db,
            tenant_id=uuid.uuid4(),
            requester_user_id=uuid.uuid4(),
            sponsor_user_id=uuid.uuid4(),
            agent_template_id=uuid.uuid4(),
            requested_name_prefix="worker",
        )
