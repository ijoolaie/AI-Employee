from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.platform_action_readiness import action_readiness


def item(tenant, status):
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant,
        correlation_id="corr-action",
        status=SimpleNamespace(value=status),
    )


def test_action_readiness_returns_status_specific_actions():
    tenant = uuid4()
    result = action_readiness(
        [item(tenant, "failed"), item(tenant, "waiting_approval"), item(tenant, "completed")],
        tenant_id=tenant,
        actor_tenant_id=tenant,
    )
    assert result[0]["actions"] == ["inspect_failure", "retry"]
    assert result[1]["actions"] == ["review_approval"]
    assert len(result) == 2


def test_action_readiness_rejects_cross_tenant_actor():
    tenant = uuid4()
    with pytest.raises(PermissionError, match="tenant mismatch"):
        action_readiness([], tenant_id=tenant, actor_tenant_id=uuid4())
