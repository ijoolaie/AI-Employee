"""Phase 7 — Invoice Employee service unit tests."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.services.invoice_service import (
    ALLOWED_STATUSES,
    _compute_totals,
    _money,
    _next_number_fallback,
    _render_invoice_pdf,
    normalize_tax_rate,
)
from app.models.business_invoice import BusinessInvoice


def test_money_rounds_half_up():
    assert _money(Decimal("1.005")) == Decimal("1.01")
    assert _money(Decimal("1.004")) == Decimal("1.00")


def test_compute_totals_basic():
    subtotal, tax, total, lines = _compute_totals(
        [{"description": "Service", "quantity": 2, "unit_price": 100}],
        Decimal("9"),
    )
    assert subtotal == Decimal("200.00")
    assert tax == Decimal("18.00")
    assert total == Decimal("218.00")
    assert lines[0]["amount"] == 200.0


def test_compute_totals_rejects_empty_description():
    with pytest.raises(ValidationAppError):
        _compute_totals([{"description": "  ", "quantity": 1, "unit_price": 10}], Decimal("0"))


def test_compute_totals_rejects_bad_qty():
    with pytest.raises(ValidationAppError):
        _compute_totals(
            [{"description": "X", "quantity": 0, "unit_price": 10}], Decimal("0")
        )


def test_allowed_statuses():
    assert "paid" in ALLOWED_STATUSES
    assert "draft" in ALLOWED_STATUSES


def test_next_number_fallback_prefix():
    assert _next_number_fallback().startswith("INV-")


def test_render_invoice_pdf_bytes():
    inv = BusinessInvoice(
        id=uuid4(),
        tenant_id=uuid4(),
        number="INV-TEST-1",
        status="draft",
        currency="IRR",
        customer_name="Acme Co",
        customer_email="a@b.com",
        issue_date=date.today(),
        due_date=None,
        tax_rate=Decimal("9"),
        subtotal=Decimal("100"),
        tax_amount=Decimal("9"),
        total=Decimal("109"),
        line_items=[
            {"description": "Consulting", "quantity": 1, "unit_price": 100, "amount": 100}
        ],
        notes="Thanks",
        metadata_={},
    )
    pdf = _render_invoice_pdf(inv)
    assert isinstance(pdf, (bytes, bytearray))
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 100


def test_normalize_tax_rate_fraction():
    assert normalize_tax_rate("0.09") == Decimal("9.00")
    assert normalize_tax_rate(0.09) == Decimal("9.00")


def test_normalize_tax_rate_percent_points():
    assert normalize_tax_rate(9) == Decimal("9")
    assert normalize_tax_rate("9") == Decimal("9")
    assert normalize_tax_rate(0) == Decimal("0")


def test_normalize_tax_rate_rejects_over_100():
    with pytest.raises(ValidationAppError):
        normalize_tax_rate(150)


def test_compute_totals_with_normalized_fraction():
    rate = normalize_tax_rate(0.09)
    subtotal, tax, total, _ = _compute_totals(
        [{"description": "Service", "quantity": 2, "unit_price": 150}],
        rate,
    )
    assert subtotal == Decimal("300.00")
    assert tax == Decimal("27.00")
    assert total == Decimal("327.00")


def test_compatibility_facade_exports_private_money_helpers():
    # Regression: ``from module import *`` intentionally excludes underscore
    # names, but Order Employee imports these helpers from the facade.
    from app.services.invoice_service import _compute_totals as compute_totals
    from app.services.invoice_service import normalize_tax_rate as normalize_rate

    assert compute_totals is not None
    assert normalize_rate is not None
