from uuid import uuid4

import pytest

from app.services.platform_correlation_drilldown import correlation_drilldown


def test_correlation_drilldown_filters_tenant_and_correlation_and_secrets():
    tenant, other = uuid4(), uuid4()
    events = [
        {"tenant_id": str(tenant), "correlation_id": "corr-1", "recorded_at": "2026-08-29T10:02:00+00:00", "api_token": "hidden"},
        {"tenant_id": str(tenant), "correlation_id": "corr-2", "recorded_at": "2026-08-29T10:01:00+00:00"},
        {"tenant_id": str(other), "correlation_id": "corr-1", "recorded_at": "2026-08-29T10:00:00+00:00"},
    ]
    result = correlation_drilldown(
        events, tenant_id=tenant, actor_tenant_id=tenant, correlation_id="corr-1"
    )
    assert len(result) == 1
    assert "api_token" not in result[0]


def test_correlation_drilldown_rejects_cross_tenant_actor():
    tenant = uuid4()
    with pytest.raises(PermissionError, match="tenant mismatch"):
        correlation_drilldown([], tenant_id=tenant, actor_tenant_id=uuid4(), correlation_id="x")
