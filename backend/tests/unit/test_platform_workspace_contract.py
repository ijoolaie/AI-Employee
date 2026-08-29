from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.platform_workspace_contract import platform_workspace_summary


def item(tenant, status):
    return SimpleNamespace(
        id=uuid4(), tenant_id=tenant, correlation_id="corr-workspace",
        status=SimpleNamespace(value=status),
        executor_type=SimpleNamespace(value="agent"), output_data={},
    )


def test_platform_workspace_allows_platform_operator():
    tenant = uuid4()
    result = platform_workspace_summary(
        [item(tenant, "failed")],
        tenant_id=tenant, actor_tenant_id=tenant, actor_role="platform_operator",
    )
    assert result["overview"]["total_work_items"] == 1


def test_platform_workspace_rejects_unprivileged_role():
    tenant = uuid4()
    with pytest.raises(PermissionError, match="platform workspace role"):
        platform_workspace_summary(
            [], tenant_id=tenant, actor_tenant_id=tenant, actor_role="client_user"
        )
