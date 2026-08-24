from datetime import datetime
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1 import employees
from app.core.exceptions import ValidationAppError


VALID_SCHEMA = {
    "type": "object",
    "properties": {
        "input": {"type": "string"},
    },
}


def _employee():
    employee = SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        slug="sales-agent",
        name="Sales Agent",
        kind="custom",
        is_active=True,
        created_at=datetime.now(),
    )
    return employee


def _version(employee_id):
    return SimpleNamespace(
        id=uuid.uuid4(),
        employee_id=employee_id,
        version_number=2,
        is_current=True,
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="test",
        allowed_tools=["calculator"],
        rules={},
        created_at=datetime.now(),
    )


@pytest.mark.asyncio
async def test_create_employee_endpoint_delegates_to_service(monkeypatch):
    employee = _employee()

    service_mock = AsyncMock(return_value=employee)
    monkeypatch.setattr(
        employees.employee_service,
        "create_employee",
        service_mock,
    )

    ctx = SimpleNamespace(
        tenant_id=employee.tenant_id,
        user_id=uuid.uuid4(),
    )
    db = object()

    payload = SimpleNamespace(
        slug="sales-agent",
        name="Sales Agent",
        kind="custom",
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="test",
        allowed_tools=["calculator"],
        rules={},
        created_at=datetime.now(),
    )

    response = await employees.create_employee(payload, ctx, db)

    assert response.success is True
    assert response.data.id == employee.id

    service_mock.assert_awaited_once_with(
        db,
        tenant_id=ctx.tenant_id,
        slug=payload.slug,
        name=payload.name,
        kind=payload.kind,
        input_schema=payload.input_schema,
        output_schema=payload.output_schema,
        prompt_template=payload.prompt_template,
        allowed_tools=payload.allowed_tools,
        rules=payload.rules,
        actor_id=ctx.user_id,
    )


@pytest.mark.asyncio
async def test_create_employee_endpoint_propagates_unregistered_tool_error(monkeypatch):
    error = ValidationAppError(
        "Employee references unregistered tools",
        details={"unknown_tools": ["secret_tool"]},
    )

    service_mock = AsyncMock(side_effect=error)
    monkeypatch.setattr(
        employees.employee_service,
        "create_employee",
        service_mock,
    )

    ctx = SimpleNamespace(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )

    payload = SimpleNamespace(
        slug="blocked-agent",
        name="Blocked Agent",
        kind="custom",
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="test",
        allowed_tools=["secret_tool"],
        rules={},
    )

    with pytest.raises(ValidationAppError) as exc_info:
        await employees.create_employee(payload, ctx, object())

    assert "unregistered tools" in str(exc_info.value)


@pytest.mark.asyncio
async def test_publish_version_endpoint_delegates_to_service(monkeypatch):
    employee_id = uuid.uuid4()
    version = _version(employee_id)

    service_mock = AsyncMock(return_value=version)
    monkeypatch.setattr(
        employees.employee_service,
        "publish_new_version",
        service_mock,
    )

    ctx = SimpleNamespace(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )

    payload = SimpleNamespace(
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="updated prompt",
        allowed_tools=["calculator"],
        rules={"max_steps": 3},
    )

    db = object()

    response = await employees.publish_version(
        employee_id,
        payload,
        ctx,
        db,
    )

    assert response.success is True
    assert response.data.id == version.id
    assert response.data.version_number == 2

    service_mock.assert_awaited_once_with(
        db,
        employee_id=employee_id,
        tenant_id=ctx.tenant_id,
        input_schema=payload.input_schema,
        output_schema=payload.output_schema,
        prompt_template=payload.prompt_template,
        allowed_tools=payload.allowed_tools,
        rules=payload.rules,
        actor_id=ctx.user_id,
    )


@pytest.mark.asyncio
async def test_publish_version_endpoint_propagates_unregistered_tool_error(
    monkeypatch,
):
    error = ValidationAppError(
        "Employee references unregistered tools",
        details={"unknown_tools": ["secret_tool"]},
    )

    service_mock = AsyncMock(side_effect=error)
    monkeypatch.setattr(
        employees.employee_service,
        "publish_new_version",
        service_mock,
    )

    employee_id = uuid.uuid4()

    ctx = SimpleNamespace(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )

    payload = SimpleNamespace(
        input_schema=VALID_SCHEMA,
        output_schema=VALID_SCHEMA,
        prompt_template="updated prompt",
        allowed_tools=["secret_tool"],
        rules={},
    )

    with pytest.raises(ValidationAppError) as exc_info:
        await employees.publish_version(
            employee_id,
            payload,
            ctx,
            object(),
        )

    assert "unregistered tools" in str(exc_info.value)


@pytest.mark.asyncio
async def test_available_tools_endpoint_returns_registry_tools():
    ctx = SimpleNamespace(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )

    response = await employees.list_available_tools(ctx)

    names = {tool.name for tool in response.data}

    assert response.success is True
    assert "calculator" in names
    assert "create_deal" in names
    assert "sales_pipeline_summary" in names
    assert "sales_forecast" in names
