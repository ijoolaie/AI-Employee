import inspect
from typing import get_args

from app.api.v1 import customers, invoices, products


def _ctx_permission(endpoint) -> str:
    annotation = inspect.get_annotations(endpoint, eval_str=True)["ctx"]
    metadata = get_args(annotation)[1]
    checker = metadata.dependency
    assert checker.__closure__ is not None
    return next(
        cell.cell_contents
        for cell in checker.__closure__
        if isinstance(cell.cell_contents, str) and "." in cell.cell_contents
    )


def test_customer_routes_have_explicit_rbac_boundaries():
    expected = {
        customers.list_customers: "customers.read",
        customers.get_customer: "customers.read",
        customers.update_customer: "customers.update",
    }
    assert {endpoint: _ctx_permission(endpoint) for endpoint in expected} == expected


def test_invoice_routes_have_explicit_rbac_boundaries():
    expected = {
        invoices.list_invoices: "invoices.read",
        invoices.invoice_summary: "invoices.read",
        invoices.get_invoice: "invoices.read",
        invoices.create_invoice: "invoices.create",
        invoices.update_status: "invoices.update",
        invoices.export_pdf: "invoices.export_pdf",
    }
    assert {endpoint: _ctx_permission(endpoint) for endpoint in expected} == expected


def test_product_routes_have_explicit_rbac_boundaries():
    expected = {
        products.list_products: "products.read",
        products.create_product: "products.create",
        products.update_inventory: "products.inventory_update",
    }
    assert {endpoint: _ctx_permission(endpoint) for endpoint in expected} == expected
