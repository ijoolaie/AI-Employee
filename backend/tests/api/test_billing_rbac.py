import inspect
from typing import get_args

from app.api.v1 import billing


def _ctx_permission(endpoint) -> str:
    annotation = inspect.get_annotations(endpoint, eval_str=True)["ctx"]
    metadata = get_args(annotation)[1]
    checker = metadata.dependency
    assert checker.__closure__ is not None
    return next(
        cell.cell_contents
        for cell in checker.__closure__
        if isinstance(cell.cell_contents, str) and cell.cell_contents.startswith("billing.")
    )


def test_billing_mutations_have_explicit_rbac_boundaries():
    expected = {
        billing.subscribe: "billing.manage",
        billing.cancel: "billing.manage",
        billing.create_checkout: "billing.manage",
        billing.create_portal: "billing.manage",
        billing.create_refund: "billing.refund",
    }
    assert {endpoint: _ctx_permission(endpoint) for endpoint in expected} == expected


def test_billing_read_routes_remain_authenticated_tenant_reads():
    for endpoint in (billing.subscription, billing.entitlements, billing.get_refund):
        annotation = inspect.get_annotations(endpoint, eval_str=True)["ctx"]
        metadata = get_args(annotation)[1]
        checker = metadata.dependency
        assert checker.__name__ == "get_current_context"
