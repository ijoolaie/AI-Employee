from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.platform_command_center import execution_overview


def item(tenant, status, executor, output=None):
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant,
        status=SimpleNamespace(value=status),
        executor_type=SimpleNamespace(value=executor),
        output_data=output,
    )


def test_command_center_aggregates_only_actor_tenant():
    tenant, other = uuid4(), uuid4()
    result = execution_overview(
        [
            item(tenant, "waiting_approval", "human", {"summary": "needs approval"}),
            item(tenant, "failed", "agent", {"api_token": "hidden", "reason": "boom"}),
            item(other, "succeeded", "agent", {}),
        ],
        tenant_id=tenant,
        actor_tenant_id=tenant,
    )

    assert result["total_work_items"] == 2
    assert result["waiting_approval"] == 1
    assert result["failed"] == 1
    assert result["evidence"][1]["output"] == {"reason": "boom"}


def test_command_center_rejects_cross_tenant_actor():
    tenant = uuid4()
    with pytest.raises(PermissionError, match="tenant mismatch"):
        execution_overview([], tenant_id=tenant, actor_tenant_id=uuid4())
