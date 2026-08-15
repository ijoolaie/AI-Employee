"""Compatibility facade for modular Invoice Employee.

New code should import from app.modules.employees.invoice.service.
Private helpers are re-exported explicitly because ``from ... import *``
does not export underscore-prefixed names.
"""
from app.modules.employees.invoice.service import (
    ALLOWED_STATUSES,
    _compute_totals,
    _money,
    _next_number_fallback,
    _render_invoice_pdf,
    create_invoice,
    financial_summary,
    get_invoice,
    list_invoices,
    normalize_tax_rate,
    update_status,
)

__all__ = [
    "ALLOWED_STATUSES",
    "_compute_totals",
    "_money",
    "_next_number_fallback",
    "_render_invoice_pdf",
    "create_invoice",
    "financial_summary",
    "get_invoice",
    "list_invoices",
    "normalize_tax_rate",
    "update_status",
]
