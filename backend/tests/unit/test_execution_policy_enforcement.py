from uuid import uuid4

import pytest

from app.services.execution_policy import ExecutionPolicy
from app.services.execution_policy import ExecutionPolicyError


def test_policy_waits_for_required_approval():
    tenant = uuid4()
    result = ExecutionPolicy.authorize(
        tenant_id=tenant,
        actor_tenant_id=tenant,
        capabilities=set(),
        requires_approval=True,
        approved=False,
    )
    assert result["authorized"] is False
    assert result["waiting_for_approval"] is True


def test_policy_rejects_concurrency_limit():
    tenant = uuid4()
    with pytest.raises(ExecutionPolicyError, match="concurrency"):
        ExecutionPolicy.authorize(
            tenant_id=tenant,
            actor_tenant_id=tenant,
            capabilities=set(),
            active_executions=2,
            concurrency_limit=2,
        )


def test_policy_rejects_secret_export_and_out_of_scope_secret():
    tenant = uuid4()
    with pytest.raises(ExecutionPolicyError, match="non-exportable"):
        ExecutionPolicy.authorize(
            tenant_id=tenant,
            actor_tenant_id=tenant,
            capabilities=set(),
            secret_names={"payments"},
            requested_secret="payments",
            export_secret=True,
        )
    with pytest.raises(ExecutionPolicyError, match="outside executor scope"):
        ExecutionPolicy.authorize(
            tenant_id=tenant,
            actor_tenant_id=tenant,
            capabilities=set(),
            requested_secret="other",
            secret_names={"payments"},
        )
