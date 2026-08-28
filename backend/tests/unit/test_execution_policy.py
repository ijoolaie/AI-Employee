from uuid import uuid4

import pytest

from app.services.execution_policy import ExecutionPolicy
from app.services.unified_execution import ExecutionError


def test_policy_authorizes_matching_tenant_capability_and_tool():
    tenant = uuid4()
    result = ExecutionPolicy.authorize(
        tenant_id=tenant,
        actor_tenant_id=tenant,
        capabilities={"refund:write"},
        required_capability="refund:write",
        tool="stripe.refund",
        allowed_tools={"stripe.refund"},
        budget_used=2.0,
        budget_limit=5.0,
    )
    assert result["authorized"] is True


def test_policy_rejects_tenant_mismatch():
    with pytest.raises(ExecutionError, match="tenant mismatch"):
        ExecutionPolicy.authorize(tenant_id=uuid4(), actor_tenant_id=uuid4(), capabilities=set())


def test_policy_rejects_missing_capability():
    with pytest.raises(ExecutionError, match="not authorized"):
        ExecutionPolicy.authorize(tenant_id:=uuid4(), actor_tenant_id=tenant_id, capabilities=set(), required_capability="refund:write")


def test_policy_rejects_out_of_scope_tool():
    tenant = uuid4()
    with pytest.raises(ExecutionError, match="outside executor scope"):
        ExecutionPolicy.authorize(tenant_id=tenant, actor_tenant_id=tenant, capabilities=set(), tool="shell", allowed_tools={"stripe.refund"})


def test_policy_rejects_budget_exhaustion():
    tenant = uuid4()
    with pytest.raises(ExecutionError, match="budget exceeded"):
        ExecutionPolicy.authorize(tenant_id=tenant, actor_tenant_id=tenant, capabilities=set(), budget_used=5.0, budget_limit=5.0)
