"""Fail-closed tenant file upload limits."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024
DEFAULT_TENANT_STORAGE_QUOTA = 500 * 1024 * 1024
DEFAULT_MAX_FILES_PER_TENANT = 1000

ALLOWED_CONTENT_TYPES = frozenset(
    {
        "text/plain",
        "text/csv",
        "application/pdf",
        "application/json",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "image/png",
        "image/jpeg",
    }
)

ALLOWED_EXTENSIONS = frozenset(
    {".txt", ".csv", ".pdf", ".json", ".docx", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"}
)


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value < 1:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def max_file_size() -> int:
    return _positive_int("MAX_FILE_SIZE_BYTES", DEFAULT_MAX_FILE_SIZE)


def tenant_storage_quota() -> int:
    return _positive_int("TENANT_STORAGE_QUOTA_BYTES", DEFAULT_TENANT_STORAGE_QUOTA)


def max_files_per_tenant() -> int:
    return _positive_int("MAX_FILES_PER_TENANT", DEFAULT_MAX_FILES_PER_TENANT)


def validate_filename(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("File extension is not allowed")


def validate_content_type(content_type: str | None, filename: str) -> None:
    if content_type and content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise ValueError("File content type is not allowed")
    # Require an allowlisted extension even when the client omits MIME metadata.
    validate_filename(filename)
