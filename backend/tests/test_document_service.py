"""Phase 5 — Document Employee analysis-engine unit tests.

Dependency-light by design (same rationale as test_report_service.py):
these exercise the pure/local functions in app.services.document_service
directly, using synthetic in-memory PDFs/images, so they run without
PostgreSQL/Redis. The DB-backed path (analyze_document() end-to-end:
FileObject read/write via Object Storage, audit_service.record) is NOT
exercised here and remains environment-dependent — see
documents/63_PHASE_5_DOCUMENT_EMPLOYEE_AS_BUILT_v0.5.0.md verification
boundary.

The OCR-path test is marked ``requires_ocr`` because the production-like
OCR runtime lives in the API container, not on the GitHub host runner.
"""

import io

import pytest

from app.core.exceptions import ValidationAppError
from app.services import document_service


def _make_native_pdf(text: str) -> bytes:
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 700, text)
    c.save()
    return buf.getvalue()


def _make_ocr_image(text: str) -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (900, 150), color="white")
    d = ImageDraw.Draw(img)
    d.text((10, 40), text, fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_extract_text_from_native_pdf_uses_native_source():
    raw = _make_native_pdf("Contract Agreement between Party A and Party B dated 2026-01-15")
    pages = document_service._extract_text_from_pdf(raw)
    assert len(pages) == 1
    assert pages[0]["source"] == "native"
    assert "Contract" in pages[0]["text"]


@pytest.mark.requires_ocr
def test_extract_text_from_image_uses_ocr_source():
    raw = _make_ocr_image("Dear customer contact test@example.com dated 2026/05/01")
    pages = document_service._extract_text_from_image(raw)
    assert len(pages) == 1
    assert pages[0]["source"] == "ocr"
    assert "test@example.com" in pages[0]["text"] or "example.com" in pages[0]["text"]


def test_extract_text_from_plain_text_bytes():
    pages = document_service._extract_text_from_plain("Hello world".encode("utf-8"))
    assert pages[0]["text"] == "Hello world"


def test_dispatch_extraction_rejects_unsupported_type():
    with pytest.raises(ValidationAppError):
        document_service._dispatch_extraction(b"binary junk", "archive.zip", "application/zip")


def test_detect_fields_finds_email_and_date():
    text = "Please contact billing@acme.com regarding invoice dated 2026-03-10 for 500,000 ریال."
    detected = document_service._detect_fields(text)
    assert "billing@acme.com" in detected["emails"]
    assert "2026-03-10" in detected["dates"]
    assert "amounts" in detected


def test_detect_fields_finds_phone_number():
    text = "Reach us at 09121234567 or 021-88776655."
    detected = document_service._detect_fields(text)
    assert "phone_numbers" in detected
    assert any("0912" in m for m in detected["phone_numbers"])


def test_classify_document_type_contract_keywords():
    text = "این قرارداد میان طرفین منعقد می‌گردد. ماده ۱: تعهدات طرف اول..."
    assert document_service._classify_document_type(text) == "contract"


def test_classify_document_type_letter_keywords():
    text = "با سلام و احتراما، به استحضار می‌رساند که..."
    assert document_service._classify_document_type(text) == "letter"


def test_classify_document_type_defaults_to_administrative():
    text = "1234567890 misc numbers only, no distinctive keywords here"
    assert document_service._classify_document_type(text) == "administrative_document"


def test_extract_text_from_pdf_rejects_too_many_pages():
    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(document_service.MAX_PAGES + 1):
        writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    with pytest.raises(ValidationAppError):
        document_service._extract_text_from_pdf(buf.getvalue())
