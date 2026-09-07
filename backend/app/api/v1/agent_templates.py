"""Stage 8 governed AgentTemplate lifecycle and installation endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import TenantContext, require_permission
from app.models.agent_instance import AgentInstanceStatus
from app.models.agent_template import AgentTemplate
from app.services.agent_template_service import (
    create_template,
    provision_instance,
    publish_template,
    transition_instance,
)
from app.services.audit_service import record

router = APIRouter(prefix="/agent-templates", tags=["agent-templates"])


class AgentTemplateCreate(BaseModel):
    agent_definition_id: UUID
    slug: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    version: int = Field(default=1, ge=1)
    risk_tier: int = Field(default=0, ge=0, le=4)
    capability_contract: dict = Field(default_factory=dict)
    permission_policy: dict = Field(default_factory=dict)
    approval_policy: dict = Field(default_factory=dict)
    evaluation_policy: dict = Field(default_factory=dict)
    install_policy: dict = Field(default_factory=dict)
    is_system_template: bool = False


class AgentTemplateRead(BaseModel):
    id: UUID
    tenant_id: UUID
    agent_definition_id: UUID
    slug: str
    name: str
    description: str | None
    version: int
    status: str
    risk_tier: int
    capability_contract: dict
    permission_policy: dict
    approval_policy: dict
    evaluation_policy: dict
    install_policy: dict
    is_system_template: bool
    published_at: datetime | None
    retired_at: datetime | None


class AgentTemplateProvisionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sponsor_user_id: UUID
    configuration: dict = Field(default_factory=dict)


class AgentInstanceLifecycleRequest(BaseModel):
    target_status: AgentInstanceStatus
    requested_by_user_id: UUID


class AgentInstanceRead(BaseModel):
    id: UUID
    tenant_id: UUID
    agent_definition_id: UUID
    agent_template_id: UUID | None
    sponsor_user_id: UUID | None
    name: str
    configuration: dict
    permission_policy: dict
    approval_policy: dict
    risk_tier: int
    status: str
    max_concurrency: int
    budget_policy: dict
    enabled: bool


def _template(item: AgentTemplate) -> AgentTemplateRead:
    return AgentTemplateRead.model_validate(item, from_attributes=True)


def _http_error(exc: Exception) -> HTTPException:
    message = str(exc)
    if "not found" in message.lower():
        code = status.HTTP_404_NOT_FOUND
    elif "required" in message.lower() or "must" in message.lower() or "between" in message.lower():
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=message)


@router.post("", response_model=AgentTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_agent_template(
    payload: AgentTemplateCreate,
    ctx: TenantContext = Depends(require_permission("agent_template.create")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await create_template(
            db,
            tenant_id=ctx.tenant_id,
            agent_definition_id=payload.agent_definition_id,
            slug=payload.slug,
            name=payload.name,
            description=payload.description,
            version=payload.version,
            risk_tier=payload.risk_tier,
            capability_contract=payload.capability_contract,
            permission_policy=payload.permission_policy,
            approval_policy=payload.approval_policy,
            evaluation_policy=payload.evaluation_policy,
            install_policy=payload.install_policy,
            is_system_template=payload.is_system_template,
        )
        await record(db, action="agent_template.created", actor_id=ctx.user_id, tenant_id=ctx.tenant_id, resource_type="agent_template", resource_id=item.id, metadata={"slug": item.slug, "version": item.version, "risk_tier": item.risk_tier})
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http_error(exc) from exc
    return _template(item)


@router.get("", response_model=list[AgentTemplateRead])
async def list_agent_templates(
    ctx: TenantContext = Depends(require_permission("agent_template.read")),
    db: AsyncSession = Depends(get_db),
    template_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    stmt = select(AgentTemplate).where(AgentTemplate.tenant_id == ctx.tenant_id).order_by(AgentTemplate.created_at.desc()).limit(limit).offset(offset)
    if template_status:
        stmt = stmt.where(AgentTemplate.status == template_status)
    result = await db.execute(stmt)
    return [_template(item) for item in result.scalars().all()]


@router.get("/{template_id}", response_model=AgentTemplateRead)
async def get_agent_template(
    template_id: UUID,
    ctx: TenantContext = Depends(require_permission("agent_template.read")),
    db: AsyncSession = Depends(get_db),
):
    item = (await db.execute(select(AgentTemplate).where(AgentTemplate.id == template_id, AgentTemplate.tenant_id == ctx.tenant_id))).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Agent template not found")
    return _template(item)


@router.post("/{template_id}/publish", response_model=AgentTemplateRead)
async def publish_agent_template(
    template_id: UUID,
    ctx: TenantContext = Depends(require_permission("agent_template.publish")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await publish_template(db, tenant_id=ctx.tenant_id, template_id=template_id, approved_by_user_id=ctx.user_id)
        await record(db, action="agent_template.published", actor_id=ctx.user_id, tenant_id=ctx.tenant_id, resource_type="agent_template", resource_id=item.id, metadata={"version": item.version, "risk_tier": item.risk_tier, "approval_required": True})
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http_error(exc) from exc
    return _template(item)


@router.post("/{template_id}/provision", response_model=AgentInstanceRead, status_code=status.HTTP_201_CREATED)
async def provision_agent_template(
    template_id: UUID,
    payload: AgentTemplateProvisionRequest,
    ctx: TenantContext = Depends(require_permission("agent_template.install")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await provision_instance(db, tenant_id=ctx.tenant_id, template_id=template_id, name=payload.name, sponsor_user_id=payload.sponsor_user_id, approved_by_user_id=ctx.user_id, configuration=payload.configuration)
        await record(db, action="agent_instance.provisioned", actor_id=ctx.user_id, tenant_id=ctx.tenant_id, resource_type="agent_instance", resource_id=item.id, metadata={"agent_template_id": str(template_id), "sponsor_user_id": str(payload.sponsor_user_id), "risk_tier": item.risk_tier, "approval_required": True})
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http_error(exc) from exc
    return AgentInstanceRead.model_validate(item, from_attributes=True)


@router.post("/agent-instances/{instance_id}/lifecycle", response_model=AgentInstanceRead)
async def transition_agent_instance(
    instance_id: UUID,
    payload: AgentInstanceLifecycleRequest,
    ctx: TenantContext = Depends(require_permission("agent_instance.lifecycle")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await transition_instance(db, tenant_id=ctx.tenant_id, instance_id=instance_id, target_status=payload.target_status, requested_by_user_id=payload.requested_by_user_id, approved_by_user_id=ctx.user_id)
        await record(db, action="agent_instance.lifecycle_changed", actor_id=ctx.user_id, tenant_id=ctx.tenant_id, resource_type="agent_instance", resource_id=item.id, metadata={"requested_by_user_id": str(payload.requested_by_user_id), "target_status": item.status.value, "risk_tier": item.risk_tier, "approval_required": True})
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise _http_error(exc) from exc
    return AgentInstanceRead.model_validate(item, from_attributes=True)
