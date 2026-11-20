import pytest

from app.core.deps import _portal_context_path_is_denied


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/edition/vendor/resellers",
        "/api/v1/edition/reseller/action-grants",
        "/api/v1/edition/licenses/vendor",
        "/api/v1/admin/users",
        "/api/v1/tenant-admin/users",
        "/api/v1/billing/subscription",
        "/api/v1/analytics/roi",
    ],
)
def test_portal_context_rejects_control_plane_and_account_routes(path: str):
    assert _portal_context_path_is_denied(path)


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/auth/me",
        "/api/v1/operations/audit-logs",
        "/api/v1/operations/metrics",
        "/api/v1/operations/dead-letters",
        "/api/v1/operations/dead-letters/00000000-0000-0000-0000-000000000001/replay",
        "/api/v1/files",
        "/api/v1/employees",
        "/api/v1/editionary/example",
        "/api/v1/administered/example",
        "/api/v1/usage/summary",
        "/api/v1/usage/optimization",
        "/api/v1/usage/cost-forecast",
        "/api/v1/usageful/example",
    ],
)
def test_portal_context_keeps_identity_and_tenant_data_routes_separate(path: str):
    assert not _portal_context_path_is_denied(path)
