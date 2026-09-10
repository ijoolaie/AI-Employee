import inspect
from typing import get_args

from app.api.v1 import commerce_integrations


EXPECTED_PERMISSION = "commerce.integration.manage"


def _ctx_permission(endpoint) -> str:
    annotation = inspect.get_annotations(endpoint, eval_str=True)["ctx"]
    metadata = get_args(annotation)[1]
    checker = metadata.dependency
    assert checker.__closure__ is not None
    return next(cell.cell_contents for cell in checker.__closure__ if cell.cell_contents == EXPECTED_PERMISSION)


def test_commerce_lifecycle_routes_require_manage_permission():
    endpoints = (
        commerce_integrations.list_integrations,
        commerce_integrations.create_integration,
        commerce_integrations.shopify_install,
        commerce_integrations.test_integration,
        commerce_integrations.sync_products,
        commerce_integrations.sync_orders,
        commerce_integrations.reconcile,
    )

    assert all(_ctx_permission(endpoint) == EXPECTED_PERMISSION for endpoint in endpoints)


def test_shopify_callback_has_no_direct_request_auth_but_requires_issued_state():
    # OAuth callback is provider-redirected and therefore cannot use the caller's
    # bearer/API-key context. Authorization is intentionally inherited from the
    # short-lived, single-use state issued by shopify_install.
    assert "ctx" not in inspect.signature(commerce_integrations.shopify_callback).parameters
