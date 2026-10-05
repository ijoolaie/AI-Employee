"""W20 governed third-party Employee Marketplace lifecycle."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.agent_definition import AgentDefinition
from app.models.agent_template import AgentTemplate, AgentTemplateStatus
from app.models.employee_marketplace import (
    EmployeeMarketplaceInstallation,
    EmployeeMarketplaceInstallationStatus,
    EmployeeMarketplacePackage,
    EmployeeMarketplacePackageStatus,
)
from app.models.skill_package import SkillPackage, SkillPackageStatus
from app.services import audit_service
from app.services.agent_governance import assert_publishable_with_evidence, assert_users_belong_to_tenant


VISIBILITIES = {"private", "unlisted", "public"}
FORBIDDEN_MANIFEST_KEYS = {"grants_execution", "auto_activate", "bypass_approval", "provider_credentials"}


def _validate_untrusted_manifest(value: object, field: str) -> None:
    if not isinstance(value, dict):
        raise ValidationAppError(f"{field} must be an object")
    if FORBIDDEN_MANIFEST_KEYS.intersection(value):
        raise ValidationAppError(f"{field} contains forbidden execution authority")


async def publish_package(
    db: AsyncSession,
    *,
    owner_tenant_id: uuid.UUID,
    source_agent_template_id: uuid.UUID,
    slug: str,
    name: str,
    version: int,
    description: str | None,
    visibility: str,
    skill_package_ids: list[str],
    workflow_refs: list[str],
    visual_pack: dict,
    actor_id: uuid.UUID,
) -> EmployeeMarketplacePackage:
    if not slug.strip() or len(slug) > 120:
        raise ValidationAppError("employee marketplace package slug is invalid")
    if not name.strip() or len(name) > 255:
        raise ValidationAppError("employee marketplace package name is invalid")
    if version < 1:
        raise ValidationAppError("employee marketplace package version must be at least 1")
    visibility = visibility.strip().lower()
    if visibility not in VISIBILITIES:
        raise ValidationAppError("employee marketplace package visibility is invalid")
    _validate_untrusted_manifest(visual_pack, "visual_pack")

    template = (await db.execute(select(AgentTemplate).where(
        AgentTemplate.id == source_agent_template_id,
        AgentTemplate.tenant_id == owner_tenant_id,
        AgentTemplate.status == AgentTemplateStatus.PUBLISHED,
    ))).scalar_one_or_none()
    if template is None:
        raise NotFoundError("published source agent template not found")

    evidence = await assert_publishable_with_evidence(
        db, tenant_id=owner_tenant_id, template_id=template.id,
    )
    if evidence.status.value != "passed":
        raise ValidationAppError("source agent template evaluation is not passed")

    if any(not isinstance(item, str) or not item.strip() for item in skill_package_ids):
        raise ValidationAppError("skill_package_ids must contain non-empty identifiers")
    if any(not isinstance(item, str) or not item.strip() for item in workflow_refs):
        raise ValidationAppError("workflow_refs must contain non-empty identifiers")

    if skill_package_ids:
        ids = [uuid.UUID(item) for item in skill_package_ids]
        rows = (await db.execute(select(SkillPackage).where(
            SkillPackage.tenant_id == owner_tenant_id,
            SkillPackage.id.in_(ids),
            SkillPackage.status == SkillPackageStatus.PUBLISHED,
        ))).scalars().all()
        if len(rows) != len(set(ids)):
            raise ValidationAppError("every bundled skill package must be a published seller-owned package")

    duplicate = (await db.execute(select(EmployeeMarketplacePackage).where(
        EmployeeMarketplacePackage.owner_tenant_id == owner_tenant_id,
        EmployeeMarketplacePackage.slug == slug,
        EmployeeMarketplacePackage.version == version,
    ))).scalar_one_or_none()
    if duplicate is not None:
        raise ConflictError("employee marketplace package version already exists")

    package = EmployeeMarketplacePackage(
        owner_tenant_id=owner_tenant_id,
        source_agent_template_id=template.id,
        slug=slug,
        name=name.strip(),
        description=description,
        version=version,
        status=EmployeeMarketplacePackageStatus.PUBLISHED,
        visibility=visibility,
        risk_tier=template.risk_tier,
        employee_manifest={
            "agent_definition_id": str(template.agent_definition_id),
            "agent_template_id": str(template.id),
            "template_version": template.version,
            "capability_contract": template.capability_contract or {},
            "description": template.description,
            "evaluation": {
                "id": str(evidence.id),
                "suite_id": evidence.suite_id,
                "score": evidence.score,
                "evidence_hash": evidence.evidence_hash,
            },
        },
        permission_manifest={
            "requested_permissions": (template.permission_policy or {}).get("permissions", []),
            "approval_policy": template.approval_policy or {},
            "review_required_on_install": True,
            "execution_authority_granted": False,
        },
        skill_package_ids=skill_package_ids,
        workflow_refs=workflow_refs,
        visual_pack=visual_pack,
        published_at=datetime.now(timezone.utc),
    )
    db.add(package)
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=owner_tenant_id,
        actor_id=actor_id,
        action="employee_marketplace.package.published",
        resource_type="employee_marketplace_package",
        resource_id=str(package.id),
        metadata={
            "slug": package.slug,
            "version": package.version,
            "risk_tier": package.risk_tier,
            "execution_authority_granted": False,
            "provider_execution": "NOT_VERIFIED",
        },
    )
    return package


async def install_package(
    db: AsyncSession,
    *,
    buyer_tenant_id: uuid.UUID,
    package_id: uuid.UUID,
    sponsor_user_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> EmployeeMarketplaceInstallation:
    await assert_users_belong_to_tenant(
        db,
        tenant_id=buyer_tenant_id,
        user_ids={sponsor_user_id, actor_id},
        field_names={sponsor_user_id: "sponsor_user_id", actor_id: "actor_id"},
    )
    package = (await db.execute(select(EmployeeMarketplacePackage).where(
        EmployeeMarketplacePackage.id == package_id,
        EmployeeMarketplacePackage.visibility == "public",
        EmployeeMarketplacePackage.status == EmployeeMarketplacePackageStatus.PUBLISHED,
    ))).scalar_one_or_none()
    if package is None:
        raise NotFoundError("public employee marketplace package not found")
    if package.owner_tenant_id == buyer_tenant_id:
        raise ConflictError("employee marketplace package owner cannot install into its own tenant")

    existing = (await db.execute(select(EmployeeMarketplaceInstallation).where(
        EmployeeMarketplaceInstallation.buyer_tenant_id == buyer_tenant_id,
        EmployeeMarketplaceInstallation.package_id == package.id,
    ))).scalar_one_or_none()
    if existing is not None:
        if existing.status == EmployeeMarketplaceInstallationStatus.ACTIVE:
            raise ConflictError("employee marketplace package is already installed")
        existing.status = EmployeeMarketplaceInstallationStatus.ACTIVE
        existing.revoked_at = None
        existing.sponsor_user_id = sponsor_user_id
        await db.flush()
        await audit_service.record(
            db,
            tenant_id=buyer_tenant_id,
            actor_id=actor_id,
            action="employee_marketplace.package.reactivated",
            resource_type="employee_marketplace_installation",
            resource_id=str(existing.id),
            metadata={"package_id": str(package.id), "execution_authority_granted": False},
        )
        return existing

    source_template = (await db.execute(select(AgentTemplate).where(
        AgentTemplate.id == package.source_agent_template_id,
        AgentTemplate.tenant_id == package.owner_tenant_id,
        AgentTemplate.status == AgentTemplateStatus.PUBLISHED,
    ))).scalar_one_or_none()
    if source_template is None:
        raise NotFoundError("source employee template is no longer available")

    source_definition = (await db.execute(select(AgentDefinition).where(
        AgentDefinition.id == source_template.agent_definition_id,
        AgentDefinition.tenant_id == package.owner_tenant_id,
        AgentDefinition.enabled.is_(True),
    ))).scalar_one_or_none()
    if source_definition is None:
        raise NotFoundError("source agent definition is no longer available")

    imported_definition = AgentDefinition(
        tenant_id=buyer_tenant_id,
        slug=f"marketplace-{package.slug}-{package.version}-{uuid.uuid4().hex[:8]}"[:120],
        name=source_definition.name,
        description=source_definition.description,
        version=source_definition.version,
        capabilities=source_definition.capabilities or [],
        allowed_tools=source_definition.allowed_tools or [],
        model_policy=source_definition.model_policy or {},
        input_schema=source_definition.input_schema or {},
        output_schema=source_definition.output_schema or {},
        policy_requirements={
            **(source_definition.policy_requirements or {}),
            "marketplace_installation_id": "pending",
            "execution_authority_granted": False,
            "provider_execution": "NOT_VERIFIED",
        },
        enabled=True,
    )
    db.add(imported_definition)
    await db.flush()

    imported_template = AgentTemplate(
        tenant_id=buyer_tenant_id,
        agent_definition_id=imported_definition.id,
        slug=f"marketplace-{package.slug}-{package.version}-{uuid.uuid4().hex[:8]}"[:120],
        name=package.name,
        description=package.description,
        version=package.version,
        status=AgentTemplateStatus.DRAFT,
        risk_tier=package.risk_tier,
        capability_contract=package.employee_manifest.get("capability_contract", {}),
        permission_policy={
            "requested_permissions": package.permission_manifest.get("requested_permissions", []),
            "execution_authority_granted": False,
            "marketplace_source_package_id": str(package.id),
        },
        approval_policy={
            **package.permission_manifest.get("approval_policy", {}),
            "marketplace_install_review_required": True,
        },
        evaluation_policy={"marketplace_source_evidence": package.employee_manifest.get("evaluation", {})},
        install_policy={"marketplace_imported": True, "requires_ceo_approval": True},
        is_system_template=False,
    )
    db.add(imported_template)
    await db.flush()

    installation = EmployeeMarketplaceInstallation(
        buyer_tenant_id=buyer_tenant_id,
        package_id=package.id,
        imported_agent_definition_id=imported_definition.id,
        imported_agent_template_id=imported_template.id,
        sponsor_user_id=sponsor_user_id,
        status=EmployeeMarketplaceInstallationStatus.ACTIVE,
        provider_execution_status="NOT_VERIFIED",
    )
    db.add(installation)
    await db.flush()

    imported_definition.policy_requirements = {
        **(imported_definition.policy_requirements or {}),
        "marketplace_installation_id": str(installation.id),
    }
    await db.flush()

    await audit_service.record(
        db,
        tenant_id=buyer_tenant_id,
        actor_id=actor_id,
        action="employee_marketplace.package.installed",
        resource_type="employee_marketplace_installation",
        resource_id=str(installation.id),
        metadata={
            "package_id": str(package.id),
            "seller_tenant_id": str(package.owner_tenant_id),
            "imported_agent_template_id": str(imported_template.id),
            "execution_authority_granted": False,
            "provider_execution": "NOT_VERIFIED",
        },
    )
    return installation


async def revoke_package(
    db: AsyncSession,
    *,
    buyer_tenant_id: uuid.UUID,
    installation_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> EmployeeMarketplaceInstallation:
    installation = (await db.execute(select(EmployeeMarketplaceInstallation).where(
        EmployeeMarketplaceInstallation.id == installation_id,
        EmployeeMarketplaceInstallation.buyer_tenant_id == buyer_tenant_id,
        EmployeeMarketplaceInstallation.status == EmployeeMarketplaceInstallationStatus.ACTIVE,
    ))).scalar_one_or_none()
    if installation is None:
        raise NotFoundError("active employee marketplace installation not found")
    installation.status = EmployeeMarketplaceInstallationStatus.REVOKED
    installation.revoked_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=buyer_tenant_id,
        actor_id=actor_id,
        action="employee_marketplace.package.revoked",
        resource_type="employee_marketplace_installation",
        resource_id=str(installation.id),
        metadata={
            "package_id": str(installation.package_id),
            "execution_authority_revoked": False,
            "provider_execution": "NOT_VERIFIED",
        },
    )
    return installation
