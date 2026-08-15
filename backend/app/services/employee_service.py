"""Employee + EmployeeVersion service (11_Employee_Framework §4, §6)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.logging import request_id_var
from app.models.employee import Employee, EmployeeVersion
from app.services import audit_service, billing_service
from app.services.schema_validation import validate_schema_definition


async def create_employee(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None,
    slug: str,
    name: str,
    kind: str,
    input_schema: dict[str, Any],
    output_schema: dict[str, Any],
    prompt_template: str,
    allowed_tools: list[str],
    rules: dict[str, Any],
    actor_id: uuid.UUID | None,
) -> Employee:
    if tenant_id is not None:
        await billing_service.enforce_employee_quota(db, tenant_id=tenant_id)
    validate_schema_definition(input_schema, field_name="input_schema")
    validate_schema_definition(output_schema, field_name="output_schema")

    existing = await db.execute(
        select(Employee).where(Employee.tenant_id == tenant_id, Employee.slug == slug)
    )
    if existing.scalar_one_or_none():
        raise ValidationAppError(f"Employee with slug '{slug}' already exists for this tenant")

    employee = Employee(tenant_id=tenant_id, slug=slug, name=name, kind=kind, is_active=True)
    db.add(employee)
    await db.flush()

    version = EmployeeVersion(
        employee_id=employee.id,
        version_number=1,
        is_current=True,
        input_schema=input_schema,
        output_schema=output_schema,
        prompt_template=prompt_template,
        allowed_tools=allowed_tools,
        rules=rules,
    )
    db.add(version)
    await db.flush()
    await db.refresh(employee)

    await audit_service.record(
        db,
        action="employee.created",
        actor_type="user" if actor_id else "system",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_type="employee",
        resource_id=employee.id,
        request_id=request_id_var.get(),
        metadata={"slug": slug, "version_number": 1},
    )
    return employee


async def publish_new_version(
    db: AsyncSession,
    *,
    employee_id: uuid.UUID,
    tenant_id: uuid.UUID | None,
    input_schema: dict[str, Any],
    output_schema: dict[str, Any],
    prompt_template: str,
    allowed_tools: list[str],
    rules: dict[str, Any],
    actor_id: uuid.UUID | None,
) -> EmployeeVersion:
    """Every meaningful change to Prompt/Tools/Schema is a new version;
    old versions are kept for history and Replay (11_Employee_Framework §4)."""
    validate_schema_definition(input_schema, field_name="input_schema")
    validate_schema_definition(output_schema, field_name="output_schema")

    employee = await get_employee(db, employee_id=employee_id, tenant_id=tenant_id)

    last_version_result = await db.execute(
        select(EmployeeVersion)
        .where(EmployeeVersion.employee_id == employee.id)
        .order_by(EmployeeVersion.version_number.desc())
        .limit(1)
    )
    last_version = last_version_result.scalar_one_or_none()
    next_number = (last_version.version_number if last_version else 0) + 1

    if last_version is not None:
        last_version.is_current = False

    new_version = EmployeeVersion(
        employee_id=employee.id,
        version_number=next_number,
        is_current=True,
        input_schema=input_schema,
        output_schema=output_schema,
        prompt_template=prompt_template,
        allowed_tools=allowed_tools,
        rules=rules,
    )
    db.add(new_version)
    await db.flush()
    await db.refresh(new_version)

    await audit_service.record(
        db,
        action="employee.version_published",
        actor_type="user" if actor_id else "system",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_type="employee",
        resource_id=employee.id,
        request_id=request_id_var.get(),
        metadata={"version_number": next_number},
    )
    return new_version


async def get_employee(
    db: AsyncSession, *, employee_id: uuid.UUID, tenant_id: uuid.UUID | None
) -> Employee:
    result = await db.execute(
        select(Employee).where(
            Employee.id == employee_id,
            (Employee.tenant_id == tenant_id) | (Employee.tenant_id.is_(None)),
        )
    )
    employee = result.scalar_one_or_none()
    if employee is None:
        raise NotFoundError("Employee not found")
    return employee


async def get_current_version(
    db: AsyncSession, *, employee_id: uuid.UUID
) -> EmployeeVersion:
    result = await db.execute(
        select(EmployeeVersion).where(
            EmployeeVersion.employee_id == employee_id, EmployeeVersion.is_current.is_(True)
        )
    )
    version = result.scalar_one_or_none()
    if version is None:
        raise NotFoundError("Employee has no current version")
    return version


async def list_employees(db: AsyncSession, *, tenant_id: uuid.UUID | None) -> list[Employee]:
    """System Employees (tenant_id NULL) + this tenant's Custom Employees
    (11_Employee_Framework §6)."""
    result = await db.execute(
        select(Employee)
        .where(
            Employee.is_active.is_(True),
            (Employee.tenant_id == tenant_id) | (Employee.tenant_id.is_(None)),
        )
        .order_by(Employee.created_at)
    )
    return list(result.scalars().all())
