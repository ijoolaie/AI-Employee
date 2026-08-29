from uuid import uuid4

import pytest

from app.services.platform_action_audit import action_audit_record


def test_audit_record_keeps_context_and_removes_secrets():
    tenant = uuid4()
    record = action_audit_record(
        tenant_id=tenant,
        actor_tenant_id=tenant,
        work_item_id=uuid4(),
        correlation_id="corr-audit",
        action="retry",
        metadata={"reason": "operator retry", "api_token": "hidden"},
    )
    assert record["correlation_id"] == "corr-audit"
    assert record["metadata"] == {"reason": "operator retry"}
    assert record["recorded_at"]


def test_audit_record_rejects_cross_tenant_actor():
    with pytest.raises(PermissionError, match="tenant mismatch"):
        action_audit_record(
            tenant_id=uuid4(),
            actor_tenant_id=uuid4(),
            work_item_id=uuid4(),
            correlation_id=None,
            action="inspect_queue",
        )
