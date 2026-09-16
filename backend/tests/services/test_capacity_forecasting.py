from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest

from app.services.capacity_forecasting import capacity_forecast


@pytest.mark.asyncio
async def test_capacity_forecast_fails_on_invalid_window():
    with pytest.raises(ValueError, match="window_days"):
        await capacity_forecast(AsyncMock(), tenant_id=uuid.uuid4(), window_days=0)


@pytest.mark.asyncio
async def test_capacity_forecast_is_read_only_and_uses_run_duration():
    db = AsyncMock()
    now = datetime.now(timezone.utc)
    db.scalar.side_effect = [20, 3, 2]
    db.execute.side_effect = [
        SimpleNamespace(
            all=lambda: [
                (now - timedelta(seconds=10), now),
                (now - timedelta(seconds=20), now),
            ]
        ),
        SimpleNamespace(
            scalars=lambda: SimpleNamespace(
                all=lambda: [
                    SimpleNamespace(max_concurrency=4),
                    SimpleNamespace(max_concurrency=2),
                ]
            )
        ),
    ]

    result = await capacity_forecast(
        db,
        tenant_id=uuid.uuid4(),
        window_days=10,
        horizon_days=5,
    )

    assert result.sample_count == 20
    assert result.demand_samples_per_day == 2
    assert result.average_run_duration_seconds == 15
    assert result.total_max_concurrency == 6
    assert result.total_available_slots == 4
    assert result.projected_required_concurrency == pytest.approx(2 * 15 / 86400)
    assert result.evidence_complete is True
    assert result.contract_version == "stage9-capacity-forecast-v1"
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_capacity_forecast_fails_closed_when_duration_evidence_is_missing():
    db = AsyncMock()
    db.scalar.side_effect = [10, 1, 0]
    db.execute.side_effect = [
        SimpleNamespace(all=lambda: []),
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [SimpleNamespace(max_concurrency=2)])),
    ]

    result = await capacity_forecast(db, tenant_id=uuid.uuid4())

    assert result.average_run_duration_seconds == 0
    assert result.projected_required_concurrency == 0
    assert result.evidence_complete is False
    assert any("duration" in item.lower() for item in result.rationale)
    db.commit.assert_not_awaited()
