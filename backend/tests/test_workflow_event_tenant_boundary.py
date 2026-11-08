from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services import workflow_trigger_service


@pytest.mark.asyncio
async def test_dispatch_event_rejects_cross_tenant_trigger_binding(monkeypatch):
    delivery_tenant_id = uuid4()
    trigger_tenant_id = uuid4()
    delivery = SimpleNamespace(
        id=uuid4(),
        tenant_id=delivery_tenant_id,
        trigger_id=uuid4(),
        workflow_run_id=None,
        status="accepted",
        attempts=0,
        error=None,
    )
    trigger = SimpleNamespace(
        id=delivery.trigger_id,
        tenant_id=trigger_tenant_id,
        workflow_id=uuid4(),
        is_active=True,
        created_by=uuid4(),
    )

    class _Result:
        def __init__(self, row):
            self.row = row

        def scalar_one_or_none(self):
            return self.row

    class _DB:
        def __init__(self):
            self.rows = iter((delivery, trigger))
            self.flush_count = 0

        async def execute(self, _statement):
            return _Result(next(self.rows))

        async def flush(self):
            self.flush_count += 1

    db = _DB()
    create_workflow_run = AsyncMock()
    monkeypatch.setattr(
        workflow_trigger_service.workflow_service,
        "create_workflow_run",
        create_workflow_run,
    )

    result = await workflow_trigger_service.dispatch_event(
        db,
        delivery_id=delivery.id,
    )

    assert result is delivery
    assert delivery.status == "rejected"
    assert delivery.error == {
        "message": "Trigger tenant does not match event delivery"
    }
    assert delivery.attempts == 0
    assert db.flush_count == 1
    create_workflow_run.assert_not_awaited()
