import io

import pytest

from app.services.file_policy import validate_content_type
from app.services.file_service import _LimitedReader


def test_allowed_file_types_are_explicit():
    validate_content_type("text/csv", "report.csv")
    validate_content_type("application/pdf", "report.pdf")

    with pytest.raises(ValueError):
        validate_content_type("application/x-executable", "payload.bin")
    with pytest.raises(ValueError):
        validate_content_type("text/plain", "payload.exe")


def test_limited_reader_never_exposes_more_than_limit():
    reader = _LimitedReader(io.BytesIO(b"abcdef"), 3)
    assert reader.read(1024) == b"abc"
    assert reader.read(1024) == b""
