from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.platform_attention_queue import attention_queue


def item(tenant, status):
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant,
        correlation_id="corr",
        status=SimpleNamespace(value=status),
        executor_type=SimpleNamespace(value="agent"),
    )


def test_attention_queue_prioritizes_failures_then_approvals():
    tenant = uuid4()
    queue = attention_queue(
        [item(tenant, "running"), item(tenant, "waiting_approval"), item(tenant, "failed")],
        tenant_id=tenant,
        actor_tenant_id=tenant,
    )
    assert [entry["status"] for entry in queue] == ["failed", "waiting_approval", "running"]


def test_attention_queue_is_tenant_safe():
    tenant = uuid4()
    other = uuid4()
    queue = attention_queue(
        [item(tenant, "failed"), item(other, "failed")],
        tenant_id=tenant,
        actor_tenant_id=tenant,
    )
    assert len(queue) == 1

    with pytest.raises(PermissionError, match="tenant mismatch"):
        attention_queue([], tenant_id=tenant, actor_tenant_id=other)
