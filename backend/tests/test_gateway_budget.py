from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.ai.gateway import _reserve_agent_run_budget
from app.services.usage_service import UsageLimitExceeded
from app.core.exceptions import ValidationAppError


class FakeResult:
    def __init__(self, row):
        self.row = row

    def one_or_none(self):
        return self.row


class FakeDb:
    def __init__(self, row):
        self.row = row

    async def execute(self, _statement):
        return FakeResult(self.row)


@pytest.mark.asyncio
async def test_agent_run_budget_reserves_before_model_call():
    run = SimpleNamespace(id=uuid4(), total_cost_usd=Decimal("0.40"))
    agent = SimpleNamespace(budget_policy={"max_cost_usd": "1.00", "reservation_usd": "0.25"})
    locked_run, reservation = await _reserve_agent_run_budget(FakeDb((run, agent)), run_id=run.id)
    assert locked_run is run
    assert reservation == Decimal("0.25")


@pytest.mark.asyncio
async def test_agent_run_budget_hard_stops_when_reservation_would_exceed_limit():
    run = SimpleNamespace(id=uuid4(), total_cost_usd=Decimal("0.80"))
    agent = SimpleNamespace(budget_policy={"max_cost_usd": "1.00", "reservation_usd": "0.25"})
    with pytest.raises(UsageLimitExceeded, match="budget exhausted"):
        await _reserve_agent_run_budget(FakeDb((run, agent)), run_id=run.id)


@pytest.mark.asyncio
async def test_configured_agent_budget_requires_positive_reservation():
    run = SimpleNamespace(id=uuid4(), total_cost_usd=Decimal("0"))
    agent = SimpleNamespace(budget_policy={"max_cost_usd": "1.00"})
    with pytest.raises(ValidationAppError, match="positive reservation"):
        await _reserve_agent_run_budget(FakeDb((run, agent)), run_id=run.id)


@pytest.mark.asyncio
async def test_unconfigured_agent_budget_is_backward_compatible():
    run = SimpleNamespace(id=uuid4(), total_cost_usd=Decimal("99"))
    agent = SimpleNamespace(budget_policy={})
    locked_run, reservation = await _reserve_agent_run_budget(FakeDb((run, agent)), run_id=run.id)
    assert locked_run is run
    assert reservation == Decimal("0")
