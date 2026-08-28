from uuid import uuid4

import pytest

from app.workers import run_worker


@pytest.mark.asyncio
async def test_phase84_worker_task_propagates_explicit_tenant_context(monkeypatch):
    run_id = str(uuid4())
    tenant_id = str(uuid4())
    captured = {}

    async def fake_run_async(received_run_id, received_tenant_id):
        captured["run_id"] = received_run_id
        captured["tenant_id"] = received_tenant_id

    monkeypatch.setattr(run_worker, "_run_async", fake_run_async)

    run_worker.execute_run_task(run_id, tenant_id)

    assert captured == {"run_id": run_id, "tenant_id": tenant_id}
