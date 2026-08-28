from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.execution_telemetry import ExecutionEvent
from app.services.execution_workspace import ExecutionWorkspace


def test_workspace_projection_preserves_lifecycle_and_correlation():
    tenant, work_item_id = uuid4(), uuid4()
    item = SimpleNamespace(
        id=work_item_id,
        status=SimpleNamespace(value="waiting_approval"),
        executor_type=SimpleNamespace(value="agent"),
        executor_id=uuid4(),
        policy_context={"approved": False},
    )
    telemetry = [
        ExecutionEvent(
            tenant_id=tenant,
            work_item_id=work_item_id,
            event="started",
            correlation_id="corr-1",
            metadata={"region": "eu", "api_secret": "hidden"},
        )
    ]

    result = ExecutionWorkspace.project(
        tenant_id=tenant,
        actor_tenant_id=tenant,
        work_item=item,
        telemetry=telemetry,
    )

    assert result["waiting_for_approval"] is True
    assert result["telemetry"][0]["correlation_id"] == "corr-1"
    assert result["telemetry"][0]["metadata"] == {"region": "eu"}


def test_workspace_rejects_cross_tenant_access():
    item = SimpleNamespace(
        id=uuid4(),
        status=SimpleNamespace(value="ready"),
        executor_type=SimpleNamespace(value="human"),
        executor_id=uuid4(),
        policy_context={},
    )

    with pytest.raises(PermissionError, match="tenant mismatch"):
        ExecutionWorkspace.project(
            tenant_id=uuid4(),
            actor_tenant_id=uuid4(),
            work_item=item,
        )
