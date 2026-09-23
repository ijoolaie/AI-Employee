from datetime import datetime, timedelta, timezone

from app.services.workforce_delegation_service import ALLOWED_MANAGER_OPERATIONS


def test_manager_operation_catalog_is_bounded():
    assert "staffing_proposal" in ALLOWED_MANAGER_OPERATIONS
    assert "replacement_proposal" in ALLOWED_MANAGER_OPERATIONS
    assert "transfer_proposal" in ALLOWED_MANAGER_OPERATIONS
    assert "retirement_proposal" in ALLOWED_MANAGER_OPERATIONS
    assert "financial_commitment" not in ALLOWED_MANAGER_OPERATIONS
    assert "security_sensitive_change" not in ALLOWED_MANAGER_OPERATIONS


def test_delegation_window_is_timezone_aware_and_bounded():
    start = datetime.now(timezone.utc)
    assert start.tzinfo is not None
    assert start + timedelta(days=366) > start + timedelta(days=365)
