"""Governed execution of tenant-installed SkillPackages."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.employee import Employee
from app.models.skill_package import (
    EmployeeSkillInstallation,
    EmployeeSkillInstallationStatus,
    SkillPackage,
    SkillPackageStatus,
)
from app.services import audit_service
from app.services.skill_purchase_entitlement_service import assert_owned
from app.services.skill_provider import get_configured_skill_provider


async def execute_installed_skill(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    skill_package_id: uuid.UUID,
    input_data: dict[str, Any],
    actor_id: uuid.UUID | None,
    request_id: str,
) -> dict[str, Any]:
    if not isinstance(input_data, dict):
        raise ValidationAppError("skill input must be an object")
    if len(input_data) > 50:
        raise ValidationAppError("skill input contains too many properties")

    employee = (
        await db.execute(
            select(Employee).where(
                Employee.id == employee_id,
                Employee.tenant_id == tenant_id,
                Employee.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if employee is None:
        raise NotFoundError("employee not found in tenant")

    installation = (
        await db.execute(
            select(EmployeeSkillInstallation).where(
                EmployeeSkillInstallation.tenant_id == tenant_id,
                EmployeeSkillInstallation.employee_id == employee_id,
                EmployeeSkillInstallation.skill_package_id == skill_package_id,
                EmployeeSkillInstallation.status == EmployeeSkillInstallationStatus.ACTIVE,
            )
        )
    ).scalar_one_or_none()
    if installation is None:
        raise ConflictError("skill package is not installed for this employee")

    package = (
        await db.execute(
            select(SkillPackage).where(
                SkillPackage.id == skill_package_id,
                SkillPackage.tenant_id == installation.source_owner_tenant_id,
                SkillPackage.status == SkillPackageStatus.PUBLISHED,
            )
        )
    ).scalar_one_or_none()
    if package is None:
        raise NotFoundError("published skill package not found")


    if package.product_id is not None:
        await assert_owned(
            db,
            tenant_id=tenant_id,
            employee_id=employee_id,
            skill_package_id=skill_package_id,
        )

    provider = get_configured_skill_provider()
    provider_result = provider.execute(
        tenant_id=str(tenant_id),
        employee_id=str(employee_id),
        skill_package_id=str(skill_package_id),
        skill_slug=package.slug,
        skill_version=package.version,
        input_data=input_data,
        request_id=request_id,
    )

    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="employee_skill.provider_execution",
        resource_type="employee_skill_installation",
        resource_id=str(installation.id),
        status="success",
        request_id=request_id,
        metadata={
            "employee_id": str(employee_id),
            "skill_package_id": str(skill_package_id),
            "skill_slug": package.slug,
            "skill_version": package.version,
            "provider": provider_result.provider,
            "external_execution": provider.external_execution,
            "executed": provider_result.executed,
            "presentation_only": False,
            "execution_authority_changed": False,
            "permissions_changed": False,
            "allowed_tools_changed": False,
        },
    )
    await db.flush()

    return {
        "provider": provider_result.provider,
        "executed": provider_result.executed,
        "status": provider_result.status,
        "skill_package_id": str(skill_package_id),
        "employee_id": str(employee_id),
        "result": provider_result.result,
    }
