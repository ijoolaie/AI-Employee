from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.services.workforce_delegation_service import (
    ALLOWED_MANAGER_OPERATIONS,
    create_delegation,
)


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


@pytest.mark.asyncio
async def test_create_delegation_rejects_non_delegable_operation_before_lookup():
    with pytest.raises(ValidationAppError, match="Unsupported manager delegation operations"):
        await create_delegation(
            object(),
            tenant_id=uuid4(),
            manager_agent_instance_id=uuid4(),
            delegated_by_user_id=uuid4(),
            starts_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            allowed_operations=["financial_commitment"],
        )
