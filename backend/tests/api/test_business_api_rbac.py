import inspect
from typing import get_args

from app.api.v1 import orders, sales


def _ctx_permission(endpoint) -> str:
    annotation = inspect.get_annotations(endpoint, eval_str=True)["ctx"]
    metadata = get_args(annotation)[1]
    checker = metadata.dependency
    assert checker.__closure__ is not None
    return next(cell.cell_contents for cell in checker.__closure__ if isinstance(cell.cell_contents, str) and "." in cell.cell_contents)


def test_order_routes_have_explicit_rbac_boundaries():
    expected = {
        orders.list_orders: "orders.read",
        orders.summary: "orders.read",
        orders.get_order: "orders.read",
        orders.create_order: "orders.create",
        orders.update_status: "orders.update",
        orders.link_invoice: "orders.invoice_link",
    }
    assert {endpoint: _ctx_permission(endpoint) for endpoint in expected} == expected


def test_sales_routes_have_explicit_rbac_boundaries():
    expected = {
        sales.list_deals: "sales.read",
        sales.pipeline: "sales.read",
        sales.forecast: "sales.read",
        sales.get_deal: "sales.read",
        sales.create_deal: "sales.create",
        sales.update_stage: "sales.update",
    }
    assert {endpoint: _ctx_permission(endpoint) for endpoint in expected} == expected
