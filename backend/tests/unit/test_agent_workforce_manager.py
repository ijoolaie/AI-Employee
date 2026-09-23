from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import agent_workforce_manager as manager


class Result:
    def __init__(self, *, scalar_items=None, rows=None, scalar=None):
        self._scalar_items = scalar_items
        self._rows = rows
        self._scalar = scalar

    def scalars(self):
        return self

    def all(self):
        if self._scalar_items is not None:
            return self._scalar_items
        return self._rows or []

    def scalar_one_or_none(self):
        return self._scalar


class DB:
    def __init__(self, results):
        self.results = iter(results)

    async def execute(self, _statement):
        return next(self.results)


@pytest.mark.asyncio
async def test_workforce_dashboard_rejects_invalid_window():
    with pytest.raises(manager.ExecutionError, match="window_days"):
        await manager.get_workforce_dashboard(DB([]), tenant_id=uuid4(), window_days=0)


@pytest.mark.asyncio
async def test_workforce_dashboard_reports_capacity_kpi_and_sla_boundary(monkeypatch):
    agent_id = uuid4()
    agent = SimpleNamespace(
        id=agent_id,
        status=SimpleNamespace(value="enabled"),
        created_at=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(
        manager,
        "get_agent_capacity",
        lambda *args, **kwargs: {
            "max_concurrency": 2,
            "active_work_items": 1,
            "available_slots": 1,
            "accepting_work": True,
        },
    )

    db = DB(
        [
            Result(scalar_items=[agent]),
            Result(
                rows=[
                    (SimpleNamespace(value="succeeded"), 3),
                    (SimpleNamespace(value="failed"), 1),
                    (SimpleNamespace(value="running"), 2),
                ]
            ),
            Result(scalar=None),
        ]
    )

    dashboard = await manager.get_workforce_dashboard(
        db,
        tenant_id=uuid4(),
        window_days=30,
    )

    assert dashboard["agents"][0]["available_slots"] == 1
    assert dashboard["work_items"]["status_counts"]["succeeded"] == 3
    assert dashboard["work_items"]["success_rate"] == 0.75
    assert dashboard["sla"]["tracking"] == "not_configured"
    assert dashboard["sla"]["compliance_rate"] is None
