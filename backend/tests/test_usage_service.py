"""Focused tests for usage aggregation and idempotency behavior."""

import uuid

import pytest

from app.models.usage import UsageEvent
from app.schemas.usage import UsageSummaryResponse
from app.services import usage_service


def test_usage_summary_contract_accepts_empty_report():
    result = UsageSummaryResponse.model_validate(
        {
            "from_at": None,
            "to_at": None,
            "calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0,
            "avg_latency_ms": 0,
            "breakdown": [],
            "notes": [],
        }
    )
    assert result.total_tokens == 0
    assert result.breakdown == []


@pytest.mark.asyncio
async def test_record_event_returns_existing_event_for_same_tenant_and_key():
    tenant_id = uuid.uuid4()
    existing = UsageEvent(tenant_id=tenant_id, event_key="evt-1", category="ai_call")

    class Result:
        def scalar_one_or_none(self):
            return existing

    class DB:
        async def execute(self, statement):
            return Result()

    result = await usage_service.record_event(
        DB(),
        tenant_id=tenant_id,
        event_key="evt-1",
        category="ai_call",
        source_type="test",
    )

    assert result is existing


@pytest.mark.asyncio
async def test_record_event_recovers_from_concurrent_unique_violation():
    tenant_id = uuid.uuid4()
    winner = UsageEvent(tenant_id=tenant_id, event_key="evt-race", category="ai_call")
    first_lookup = True

    class Result:
        def scalar_one_or_none(self):
            return None if first_lookup else winner

    class Nested:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DB:
        def add(self, item):
            pass

        async def execute(self, statement):
            nonlocal first_lookup
            first_lookup = False
            return Result()

        async def flush(self):
            from sqlalchemy.exc import IntegrityError
            raise IntegrityError("insert", {}, Exception("duplicate"))

        def begin_nested(self):
            return Nested()

    result = await usage_service.record_event(
        DB(),
        tenant_id=tenant_id,
        event_key="evt-race",
        category="ai_call",
        source_type="test",
    )

    assert result is winner


import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from app.services.usage_service import UsageLimitExceeded, enforce_cost_limit

@pytest.mark.asyncio
async def test_cost_limit_fails_closed_for_excess_usage():
    tenant_id = uuid.uuid4(); db = AsyncMock(); result = MagicMock(); result.scalar_one.return_value = Decimal("9.50"); db.execute.return_value = result
    with pytest.raises(UsageLimitExceeded):
        await enforce_cost_limit(db, tenant_id=tenant_id, max_cost_usd=10, requested_cost_usd=1)

@pytest.mark.asyncio
async def test_cost_limit_allows_usage_within_budget():
    tenant_id = uuid.uuid4(); db = AsyncMock(); result = MagicMock(); result.scalar_one.return_value = Decimal("9.50"); db.execute.return_value = result
    await enforce_cost_limit(db, tenant_id=tenant_id, max_cost_usd=10, requested_cost_usd=0.50)
