"""Document Employee analysis engine (Phase 5 — 03_Roadmap_v1.1 §8, فاز پنجم).

Given a previously-uploaded tenant file (PDF, PNG/JPEG image, or DOCX),
this module extracts text — using native text extraction when the source
already contains a text layer (digital PDF/DOCX), and falling back to OCR
(Tesseract, English + Persian) for scanned/image-based pages — then applies
deterministic, regex-based extraction of common administrative-document
fields (dates, monetary amounts, emails, phone numbers, Iranian national ID
/ economic code shaped numbers). The extracted text and structured fields
are persisted as ordinary tenant-scoped FileObject/JSON exactly like the
Phase 2 Report Employee's artifacts — no new storage surface.

Roadmap scope for فاز پنجم (Document Employee): OCR، پردازش PDF، قرارداد،
نامه، فرم، اسناد اداری. This module deliberately stays deterministic for
the same reason report_service.py does: the calling model narrates/
classifies via the Employee prompt (contract vs. letter vs. form, a
plain-language summary, follow-up actions), but every *fact* in that
narration (dates, amounts, page count, detected fields) traces back to
this module's output, not to LLM inference — so it can't hallucinate a
number that was never in the document.

This module is invoked exclusively through the `analyze_document` Tool
(app.ai.tool_registry), which enforces tenant scoping, the `run.execute`
permission, and JSON-Schema argument validation before calling here. It is
never reachable directly from a route.
"""

from __future__ import annotations

import io
import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationAppError
from app.models.file import FileObject
from app.services import audit_service, file_service, storage

MAX_PAGES = 50
# Below this many extracted characters per page, a PDF page is treated as
# "no usable text layer" and rendered to an image for OCR instead — this is
# what makes scanned contracts/letters/forms work, not just born-digital PDFs.
MIN_CHARS_PER_PAGE_FOR_NATIVE_TEXT = 20
OCR_DPI = 200
OCR_LANGS = "eng+fas"  # English + Persian — Roadmap explicitly targets Persian admin docs

# Deliberately simple, auditable regexes — same "پیش‌بینی ساده" design
# principle as report_service._simple_forecast: a small, explainable rule
# beats an opaque model guess for facts that must be exactly right.
_PATTERNS: dict[str, re.Pattern[str]] = {
    "emails": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "phone_numbers": re.compile(r"(?:\+98|0)?9\d{9}\b|\b0\d{2,3}[-\s]?\d{7,8}\b"),
    # Gregorian dates (YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY) and Jalali-style
    # dates (13xx/xx/xx, common in Iranian administrative documents).
    "dates": re.compile(
        r"\b(?:13|14)\d{2}[/\-]\d{1,2}[/\-]\d{1,2}\b|\b\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\b|\b\d{1,2}[/\-]\d{1,2}[/\-]\d{4}\b"
    ),
    # Monetary amounts: digit groups with optional thousands separators
    # followed by a currency word/symbol (ریال/تومان/$/€/USD/IRR...).
    "amounts": re.compile(
        r"[\d,\.]{4,}\s?(?:ریال|تومان|﷼|\$|€|USD|IRR|EUR)\b|(?:\$|€)\s?[\d,\.]{2,}"
    ),
    # Iranian national ID (10 digits) / economic code (11 digits) shaped
    # sequences — flagged as *candidates*, not validated via checksum.
    "id_number_candidates": re.compile(r"\b\d{10,11}\b"),
}


def _extract_text_from_pdf(raw: bytes) -> list[dict[str, Any]]:
    """Returns one entry per page: {"page": n, "text": str, "source": "native"|"ocr"}."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(raw))
    page_count = len(reader.pages)
    if page_count > MAX_PAGES:
        raise ValidationAppError(
            f"Document has {page_count} pages; the Phase 5 limit is {MAX_PAGES}."
        )

    pages: list[dict[str, Any]] = []
    ocr_page_indices: list[int] = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if len(text) >= MIN_CHARS_PER_PAGE_FOR_NATIVE_TEXT:
            pages.append({"page": i + 1, "text": text, "source": "native"})
        else:
            pages.append({"page": i + 1, "text": "", "source": "pending_ocr"})
            ocr_page_indices.append(i)

    if ocr_page_indices:
        import pytesseract
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(
            raw,
            dpi=OCR_DPI,
            first_page=min(ocr_page_indices) + 1,
            last_page=max(ocr_page_indices) + 1,
        )
        offset = min(ocr_page_indices)
        for idx in ocr_page_indices:
            image = images[idx - offset]
            ocr_text = pytesseract.image_to_string(image, lang=OCR_LANGS).strip()
            pages[idx]["text"] = ocr_text
            pages[idx]["source"] = "ocr"

    return pages


def _extract_text_from_image(raw: bytes) -> list[dict[str, Any]]:
    import pytesseract
    from PIL import Image

    image = Image.open(io.BytesIO(raw))
    text = pytesseract.image_to_string(image, lang=OCR_LANGS).strip()
    return [{"page": 1, "text": text, "source": "ocr"}]


def _extract_text_from_docx(raw: bytes) -> list[dict[str, Any]]:
    import docx

    document = docx.Document(io.BytesIO(raw))
    text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
    return [{"page": 1, "text": text, "source": "native"}]


def _extract_text_from_plain(raw: bytes) -> list[dict[str, Any]]:
    for encoding in ("utf-8", "utf-8-sig", "cp1256", "latin-1"):
        try:
            return [{"page": 1, "text": raw.decode(encoding), "source": "native"}]
        except UnicodeDecodeError:
            continue
    raise ValidationAppError("Could not decode file as text")


def _dispatch_extraction(raw: bytes, filename: str, content_type: str | None) -> list[dict[str, Any]]:
    name = (filename or "").lower()
    ctype = content_type or ""
    if name.endswith(".pdf") or ctype == "application/pdf":
        return _extract_text_from_pdf(raw)
    if name.endswith((".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp")) or ctype.startswith("image/"):
        return _extract_text_from_image(raw)
    if name.endswith(".docx") or ctype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_text_from_docx(raw)
    if name.endswith((".txt", ".md")) or ctype.startswith("text/"):
        return _extract_text_from_plain(raw)
    raise ValidationAppError(
        "Unsupported document type for Phase 5 analysis. Supported: PDF, PNG/JPEG image, DOCX, TXT.",
        details={"filename": filename, "content_type": content_type},
    )


def _detect_fields(full_text: str) -> dict[str, list[str]]:
    detected: dict[str, list[str]] = {}
    for label, pattern in _PATTERNS.items():
        matches = pattern.findall(full_text)
        if matches:
            # De-duplicate while preserving order; cap so a noisy OCR page
            # can't blow up the response.
            seen: list[str] = []
            for m in matches:
                if m not in seen:
                    seen.append(m)
            detected[label] = seen[:25]
    return detected


def _classify_document_type(full_text: str) -> str:
    """Best-effort, keyword-based classification into the Roadmap's four
    Phase 5 document categories (قرارداد/نامه/فرم/اسناد اداری). Deliberately
    a simple keyword vote, not a model call — consistent with this module's
    "deterministic substrate" design principle."""
    lowered = full_text.lower()
    scores = {
        "contract": sum(
            1 for kw in ("قرارداد", "طرفین", "ماده", "تعهد", "contract", "agreement", "party", "clause")
            if kw in full_text or kw in lowered
        ),
        "letter": sum(
            1 for kw in ("با سلام", "احتراما", "نامه", "dear", "sincerely", "regards")
            if kw in full_text or kw in lowered
        ),
        "form": sum(
            1 for kw in ("فرم", "لطفا تکمیل", "form", "please fill", "checkbox", "☐")
            if kw in full_text or kw in lowered
        ),
    }
    best_label, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score == 0:
        return "administrative_document"
    return best_label


async def analyze_document(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    file_id: str,
) -> dict[str, Any]:
    """Core Phase 5 entry point, called by the `analyze_document` Tool handler.

    tenant_id/actor_id are always resolved server-side from the Run's
    TenantContext (never client-supplied), matching the tenant-isolation
    rule already enforced for `send_email`/`analyze_dataset` in
    app.ai.tool_registry.
    """
    try:
        source_uuid = uuid.UUID(str(file_id))
    except ValueError as exc:
        raise ValidationAppError("file_id must be a valid UUID") from exc

    source_file = await file_service.get_file(db, tenant_id=tenant_id, file_id=source_uuid)
    backend = storage.get_storage_backend()
    with backend.open(source_file.storage_key) as fh:
        raw = fh.read()

    pages = _dispatch_extraction(raw, source_file.filename, source_file.content_type)
    full_text = "\n\n".join(p["text"] for p in pages if p["text"])
    if not full_text.strip():
        raise ValidationAppError(
            "No text could be extracted from this document (native or OCR)."
        )

    detected_fields = _detect_fields(full_text)
    document_type = _classify_document_type(full_text)
    ocr_pages_used = sum(1 for p in pages if p["source"] == "ocr")

    base_name = source_file.filename.rsplit(".", 1)[0] or "document"
    extracted_text_file = await file_service.upload_file(
        db,
        tenant_id=tenant_id,
        uploaded_by=actor_id,
        filename=f"{base_name}_extracted_text.txt",
        content_type="text/plain; charset=utf-8",
        data=io.BytesIO(full_text.encode("utf-8")),
    )

    await audit_service.record(
        db,
        action="document.analyzed",
        actor_type="system",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_type="file",
        resource_id=str(source_file.id),
        metadata={
            "extracted_text_file_id": str(extracted_text_file.id),
            "page_count": len(pages),
            "ocr_pages_used": ocr_pages_used,
            "document_type": document_type,
        },
    )

    return {
        "page_count": len(pages),
        "ocr_pages_used": ocr_pages_used,
        "character_count": len(full_text),
        "document_type": document_type,
        "detected_fields": detected_fields,
        "pages": [{"page": p["page"], "source": p["source"], "char_count": len(p["text"])} for p in pages],
        "text_preview": full_text[:2000],
        "document_artifacts": {
            "extracted_text_file_id": str(extracted_text_file.id),
        },
    }
