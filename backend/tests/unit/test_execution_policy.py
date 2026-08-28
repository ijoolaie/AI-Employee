from uuid import uuid4

import pytest

from app.services.execution_policy import ExecutionPolicy
from app.services.unified_execution import ExecutionError


def test_policy_allows_authorized_tool_and_capability():
    tenant = uuid4()
    result = ExecutionPolicy.authorize(
        tenant_id=tenant,
        actor_tenant_id=tenant,
        capabilities={"refund"},
        required_capability="refund",
        tool="payments.refund",
        allowed_tools={"payments.refund"},
        budget_used=1,
        budget_limit=5,
    )
    assert result["authorized"] is True


def test_policy_rejects_cross_tenant_execution():
    with pytest.raises(ExecutionError, match="tenant mismatch"):
        ExecutionPolicy.authorize(
            tenant_id=uuid4(), actor_tenant_id=uuid4(), capabilities=set()
        )


def test_policy_rejects_missing_capability_and_tool_scope():
    tenant = uuid4()
    with pytest.raises(ExecutionError, match="capability"):
        ExecutionPolicy.authorize(
            tenant_id=tenant, actor_tenant_id=tenant, capabilities=set(),
            required_capability="refund",
        )
    with pytest.raises(ExecutionError, match="outside executor scope"):
        ExecutionPolicy.authorize(
            tenant_id=tenant, actor_tenant_id=tenant, capabilities={"refund"},
            tool="payments.refund", allowed_tools=set(),
        )


def test_policy_rejects_exceeded_budget():
    tenant = uuid4()
    with pytest.raises(ExecutionError, match="budget exceeded"):
        ExecutionPolicy.authorize(
            tenant_id=tenant, actor_tenant_id=tenant, capabilities=set(),
            budget_used=10, budget_limit=10,
        )
