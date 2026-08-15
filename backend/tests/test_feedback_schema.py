"""Phase 3 — Feedback schema validation tests (DB-independent).

The DB-backed paths (feedback_service.create_feedback / validation_summary)
require PostgreSQL and are NOT exercised here — see
documents/59_PHASE_3_VALIDATION_TOOLING_AS_BUILT_v0.4.0.md verification
boundary. These tests only cover the Pydantic contract, consistent with
how test_rbac.py keeps DB-independent tests dependency-light.
"""

import pytest
from pydantic import ValidationError

from app.schemas.feedback import FeedbackCreate


def test_feedback_create_accepts_valid_rating():
    fb = FeedbackCreate(rating=5, comment="Very useful report")
    assert fb.rating == 5
    assert fb.category == "run"


@pytest.mark.parametrize("rating", [0, 6, -1])
def test_feedback_create_rejects_out_of_range_rating(rating):
    with pytest.raises(ValidationError):
        FeedbackCreate(rating=rating)


def test_feedback_create_rejects_unknown_category():
    with pytest.raises(ValidationError):
        FeedbackCreate(rating=4, category="not-a-real-category")


def test_feedback_create_allows_general_category_without_run():
    fb = FeedbackCreate(rating=3, category="general", comment="Nice product overall")
    assert fb.run_id is None
    assert fb.employee_id is None
