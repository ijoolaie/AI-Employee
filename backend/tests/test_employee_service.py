import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ValidationAppError
from app.services import employee_service


VALID_SCHEMA = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}


@pytest.mark.asyncio
async def test_create_employee_rejects_unregistered_tool_before_db_work():
    db = AsyncMock()

    with pytest.raises(ValidationAppError) as exc_info:
        await employee_service.create_employee(
            db,
            tenant_id=uuid.uuid4(),
            slug=f"test-{uuid.uuid4().hex[:8]}",
            name="Test Employee",
            kind="custom",
            input_schema=VALID_SCHEMA,
            output_schema=VALID_SCHEMA,
            prompt_template="test",
            allowed_tools=["secret_tool"],
            rules={},
            actor_id=None,
        )

    assert "Employee references unregistered tools" in str(exc_info.value)
    assert exc_info.value.details["unknown_tools"] == ["secret_tool"]

    # Validation must fail before any DB query/flush is attempted.
    db.execute.assert_not_awaited()
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_publish_new_version_rejects_unregistered_tool_before_employee_lookup():
    db = AsyncMock()

    with pytest.raises(ValidationAppError) as exc_info:
        await employee_service.publish_new_version(
            db,
            employee_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            input_schema=VALID_SCHEMA,
            output_schema=VALID_SCHEMA,
            prompt_template="test",
            allowed_tools=["secret_tool"],
            rules={},
            actor_id=None,
        )

    assert "Employee references unregistered tools" in str(exc_info.value)
    assert exc_info.value.details["unknown_tools"] == ["secret_tool"]

    # Validation must happen before get_employee() touches the DB.
    db.execute.assert_not_awaited()
    db.flush.assert_not_awaited()
