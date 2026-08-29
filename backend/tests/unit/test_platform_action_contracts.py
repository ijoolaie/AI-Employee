from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.platform_action_contracts import PlatformActionRequest, validate_action


def item(tenant, status):
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant,
        correlation_id="corr-contract",
        status=SimpleNamespace(value=status),
    )


def test_action_contract_allows_only_state_actions():
    tenant = uuid4()
    work = item(tenant, "failed")
    request = PlatformActionRequest(tenant, work.id, work.correlation_id, "retry")
    assert validate_action(work, request, actor_tenant_id=tenant) == request

    bad = PlatformActionRequest(tenant, work.id, work.correlation_id, "review_approval")
    with pytest.raises(ValueError, match="not allowed"):
        validate_action(work, bad, actor_tenant_id=tenant)


def test_action_contract_is_tenant_safe():
    tenant = uuid4()
    work = item(tenant, "pending")
    request = PlatformActionRequest(tenant, work.id, work.correlation_id, "inspect_queue")
    with pytest.raises(PermissionError, match="tenant mismatch"):
        validate_action(work, request, actor_tenant_id=uuid4())
