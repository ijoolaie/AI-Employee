"""Phase 8 — Order Employee service unit tests."""

from decimal import Decimal

import pytest

from app.core.exceptions import ValidationAppError
from app.services.invoice_service import normalize_tax_rate
from app.services.order_service import ALLOWED_STATUSES, _next_number_fallback
from app.services.invoice_service import _compute_totals


def test_allowed_order_statuses():
    assert "confirmed" in ALLOWED_STATUSES
    assert "delivered" in ALLOWED_STATUSES
    assert "cancelled" in ALLOWED_STATUSES


def test_order_number_prefix():
    assert _next_number_fallback().startswith("ORD-")


def test_order_totals_with_fraction_tax():
    rate = normalize_tax_rate(0.09)
    subtotal, tax, total, lines = _compute_totals(
        [{"description": "Widget", "quantity": 3, "unit_price": 100}],
        rate,
    )
    assert subtotal == Decimal("300.00")
    assert tax == Decimal("27.00")
    assert total == Decimal("327.00")
    assert lines[0]["description"] == "Widget"


def test_order_totals_reject_empty_line():
    with pytest.raises(ValidationAppError):
        _compute_totals([{"description": "", "quantity": 1, "unit_price": 10}], Decimal("0"))



def test_order_number_fallback_is_collision_resistant():
    first = _next_number_fallback()
    second = _next_number_fallback()

    assert first.startswith("ORD-")
    assert second.startswith("ORD-")
    assert first != second
    assert len(first) <= 64
    assert len(second) <= 64


def test_business_order_number_is_tenant_scoped_unique():
    from app.models.business_order import BusinessOrder

    names = {constraint.name for constraint in BusinessOrder.__table__.constraints}
    assert "uq_business_orders_tenant_number" in names
