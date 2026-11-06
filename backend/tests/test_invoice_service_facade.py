"""Compatibility facade regressions for invoice API service imports."""

from app.modules.employees.invoice import service as modular_service
from app.services import invoice_service


def test_compatibility_facade_exports_invoice_pdf_export():
    # The API imports the compatibility facade, not the modular implementation.
    assert invoice_service.export_pdf is modular_service.export_pdf
