"""Compatibility facade for the modular Document Employee service."""
from app.modules.employees.document.service import *  # noqa: F401,F403
from app.modules.employees.document.service import (  # noqa: F401
    MAX_PAGES,
    _classify_document_type,
    _detect_fields,
    _dispatch_extraction,
    _extract_text_from_docx,
    _extract_text_from_image,
    _extract_text_from_pdf,
    _extract_text_from_plain,
)
