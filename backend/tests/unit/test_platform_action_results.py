from uuid import uuid4

import pytest

from app.services.platform_action_results import action_result


def test_action_result_projects_status_and_sanitizes_data():
    tenant = uuid4()
    result = action_result(
        tenant_id=tenant,
        actor_tenant_id=tenant,
        work_item_id=uuid4(),
        correlation_id="corr-result",
        action="retry",
        succeeded=False,
        result={"reason": "upstream unavailable", "api_key": "hidden"},
    )
    assert result["status"] == "failed"
    assert result["result"] == {"reason": "upstream unavailable"}


def test_action_result_rejects_cross_tenant_actor():
    with pytest.raises(PermissionError, match="tenant mismatch"):
        action_result(
            tenant_id=uuid4(),
            actor_tenant_id=uuid4(),
            work_item_id=uuid4(),
            correlation_id=None,
            action="inspect_queue",
            succeeded=True,
        )
