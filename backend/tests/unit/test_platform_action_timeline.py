from uuid import uuid4

import pytest

from app.services.platform_action_timeline import action_timeline


def test_action_timeline_is_tenant_scoped_and_chronological():
    tenant, other = uuid4(), uuid4()
    events = [
        {"tenant_id": str(tenant), "work_item_id": "a", "action": "retry", "recorded_at": "2026-08-29T10:02:00+00:00"},
        {"tenant_id": str(other), "work_item_id": "x", "action": "retry", "recorded_at": "2026-08-29T09:00:00+00:00"},
        {"tenant_id": str(tenant), "work_item_id": "b", "action": "review_approval", "recorded_at": "2026-08-29T10:01:00+00:00"},
    ]

    timeline = action_timeline(events, tenant_id=tenant, actor_tenant_id=tenant)
    assert [event["work_item_id"] for event in timeline] == ["b", "a"]


def test_action_timeline_rejects_cross_tenant_actor():
    tenant = uuid4()
    with pytest.raises(PermissionError, match="tenant mismatch"):
        action_timeline([], tenant_id=tenant, actor_tenant_id=uuid4())
