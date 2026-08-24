import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import NotFoundError, ValidationAppError
from app.services import employee_service


VALID_SCHEMA = {
    "type": "object",
    "properties": {
        "input": {"type": "string"},
    },
}


def _db():
    db = AsyncMock()

    result = SimpleNamespace(
        scalar_one_or_none=lambda: None,
    )
    db.execute.return_value = result

    return db


@pytest.mark.asyncio
async def test_create_employee_creates_initial_current_version_and_audit(monkeypatch):
    db = _db()
    audit_mock = AsyncMock()

    monkeypatch.setattr(
        employee_service.audit_service,
        "record",
        audit_mock,
    )

    employee = await employee_service.create_employee(
        db,
        tenant_id=None,
        slug=f"versioned-{uuid.uuid4().hex[:8]}",
        name="Versioned Employee",
        kind="system",
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="initial prompt",
        allowed_tools=["calculator"],
        rules={"max_steps": 3},
        actor_id=None,
    )

    assert employee.id is not None
    assert employee.is_active is True

    added_objects = [call.args[0] for call in db.add.call_args_list]

    versions = [
        obj
        for obj in added_objects
        if isinstance(obj, employee_service.EmployeeVersion)
    ]

    assert len(versions) == 1

    version = versions[0]
    assert version.employee_id == employee.id
    assert version.version_number == 1
    assert version.is_current is True
    assert version.allowed_tools == ["calculator"]

    audit_mock.assert_awaited_once()

    audit_kwargs = audit_mock.await_args.kwargs
    assert audit_kwargs["action"] == "employee.created"
    assert audit_kwargs["resource_type"] == "employee"
    assert audit_kwargs["resource_id"] == employee.id
    assert audit_kwargs["metadata"]["version_number"] == 1


@pytest.mark.asyncio
async def test_publish_new_version_makes_previous_version_not_current(monkeypatch):
    db = _db()

    employee = SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
    )

    previous_version = employee_service.EmployeeVersion(
        employee_id=employee.id,
        version_number=1,
        is_current=True,
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="v1",
        allowed_tools=["calculator"],
        rules={},
    )

    db.execute.return_value = SimpleNamespace(
        scalar_one_or_none=lambda: previous_version,
    )

    monkeypatch.setattr(
        employee_service,
        "get_employee",
        AsyncMock(return_value=employee),
    )

    audit_mock = AsyncMock()
    monkeypatch.setattr(
        employee_service.audit_service,
        "record",
        audit_mock,
    )

    new_version = await employee_service.publish_new_version(
        db,
        employee_id=employee.id,
        tenant_id=employee.tenant_id,
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="v2",
        allowed_tools=["calculator"],
        rules={"max_steps": 5},
        actor_id=uuid.uuid4(),
    )

    assert previous_version.is_current is False

    assert new_version.employee_id == employee.id
    assert new_version.version_number == 2
    assert new_version.is_current is True
    assert new_version.prompt_template == "v2"
    assert new_version.rules == {"max_steps": 5}

    audit_mock.assert_awaited_once()

    audit_kwargs = audit_mock.await_args.kwargs
    assert audit_kwargs["action"] == "employee.version_published"
    assert audit_kwargs["resource_id"] == employee.id
    assert audit_kwargs["metadata"]["version_number"] == 2


@pytest.mark.asyncio
async def test_publish_new_versions_are_sequential(monkeypatch):
    db = _db()

    employee = SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
    )

    version_2 = employee_service.EmployeeVersion(
        employee_id=employee.id,
        version_number=2,
        is_current=True,
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="v2",
        allowed_tools=["calculator"],
        rules={},
    )

    db.execute.return_value = SimpleNamespace(
        scalar_one_or_none=lambda: version_2,
    )

    monkeypatch.setattr(
        employee_service,
        "get_employee",
        AsyncMock(return_value=employee),
    )

    monkeypatch.setattr(
        employee_service.audit_service,
        "record",
        AsyncMock(),
    )

    version_3 = await employee_service.publish_new_version(
        db,
        employee_id=employee.id,
        tenant_id=employee.tenant_id,
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="v3",
        allowed_tools=["calculator"],
        rules={},
        actor_id=None,
    )

    assert version_2.is_current is False
    assert version_3.version_number == 3
    assert version_3.is_current is True


@pytest.mark.asyncio
async def test_publish_version_rejects_foreign_employee(monkeypatch):
    db = _db()

    employee_id = uuid.uuid4()
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    get_employee_mock = AsyncMock(
        side_effect=NotFoundError("Employee not found")
    )

    monkeypatch.setattr(
        employee_service,
        "get_employee",
        get_employee_mock,
    )

    with pytest.raises(NotFoundError):
        await employee_service.publish_new_version(
            db,
            employee_id=employee_id,
            tenant_id=tenant_a,
            input_schema=VALID_SCHEMA,
            output_schema=VALID_SCHEMA,
            prompt_template="blocked",
            allowed_tools=["calculator"],
            rules={},
            actor_id=None,
        )

    get_employee_mock.assert_awaited_once_with(
        db,
        employee_id=employee_id,
        tenant_id=tenant_a,
    )

    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_publish_version_rejects_unregistered_tool_before_employee_lookup(
    monkeypatch,
):
    db = _db()

    get_employee_mock = AsyncMock()
    monkeypatch.setattr(
        employee_service,
        "get_employee",
        get_employee_mock,
    )

    with pytest.raises(ValidationAppError) as exc_info:
        await employee_service.publish_new_version(
            db,
            employee_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            input_schema=VALID_SCHEMA,
            output_schema=VALID_SCHEMA,
            prompt_template="blocked",
            allowed_tools=["secret_tool"],
            rules={},
            actor_id=None,
        )

    assert "unregistered tools" in str(exc_info.value)
    assert exc_info.value.details["unknown_tools"] == ["secret_tool"]

    get_employee_mock.assert_not_awaited()
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_publish_version_audits_correct_version_number(monkeypatch):
    db = _db()

    employee = SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
    )

    previous_version = employee_service.EmployeeVersion(
        employee_id=employee.id,
        version_number=7,
        is_current=True,
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="v7",
        allowed_tools=["calculator"],
        rules={},
    )

    db.execute.return_value = SimpleNamespace(
        scalar_one_or_none=lambda: previous_version,
    )

    monkeypatch.setattr(
        employee_service,
        "get_employee",
        AsyncMock(return_value=employee),
    )

    audit_mock = AsyncMock()
    monkeypatch.setattr(
        employee_service.audit_service,
        "record",
        audit_mock,
    )

    actor_id = uuid.uuid4()

    version = await employee_service.publish_new_version(
        db,
        employee_id=employee.id,
        tenant_id=employee.tenant_id,
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="v8",
        allowed_tools=["calculator"],
        rules={},
        actor_id=actor_id,
    )

    assert version.version_number == 8
    assert version.is_current is True
    assert previous_version.is_current is False

    audit_kwargs = audit_mock.await_args.kwargs
    assert audit_kwargs["action"] == "employee.version_published"
    assert audit_kwargs["actor_type"] == "user"
    assert audit_kwargs["actor_id"] == actor_id
    assert audit_kwargs["tenant_id"] == employee.tenant_id
    assert audit_kwargs["metadata"] == {"version_number": 8}
