"""W20 third-party Employee Marketplace API."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import TenantContext, require_permission
from app.schemas.employee_marketplace import (
    EmployeeMarketplaceInstallationRead,
    EmployeeMarketplaceInstallRequest,
    EmployeeMarketplacePackageCreate,
    EmployeeMarketplacePackageRead,
)
from app.services.employee_marketplace_service import install_package, publish_package, revoke_package

router = APIRouter(prefix="/employee-marketplace", tags=["employee-marketplace"])


def _err(exc: Exception) -> HTTPException:
    msg = str(exc)
    code = status.HTTP_404_NOT_FOUND if "not found" in msg.lower() else (
        status.HTTP_422_UNPROCESSABLE_ENTITY if "invalid" in msg.lower() or "must" in msg.lower() else status.HTTP_409_CONFLICT
    )
    return HTTPException(status_code=code, detail=msg)


@router.post("/packages", response_model=EmployeeMarketplacePackageRead, status_code=status.HTTP_201_CREATED)
async def create_package(
    payload: EmployeeMarketplacePackageCreate,
    ctx: TenantContext = Depends(require_permission("employee_marketplace.publish")),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    try:
        item = await publish_package(
            db,
            owner_tenant_id=ctx.tenant_id,
            source_agent_template_id=payload.source_agent_template_id,
            slug=payload.slug,
            name=payload.name,
            version=payload.version,
            description=payload.description,
            visibility=payload.visibility,
            skill_package_ids=payload.skill_package_ids,
            workflow_refs=payload.workflow_refs,
            visual_pack=payload.visual_pack,
            actor_id=ctx.user_id,
        )
        await db.commit()
        return item
    except Exception as exc:
        await db.rollback()
        raise _err(exc) from exc


@router.post("/packages/{package_id}/install", response_model=EmployeeMarketplaceInstallationRead, status_code=status.HTTP_201_CREATED)
async def install(
    package_id: UUID,
    payload: EmployeeMarketplaceInstallRequest,
    ctx: TenantContext = Depends(require_permission("employee_marketplace.install")),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    try:
        item = await install_package(
            db,
            buyer_tenant_id=ctx.tenant_id,
            package_id=package_id,
            sponsor_user_id=payload.sponsor_user_id,
            actor_id=ctx.user_id,
        )
        await db.commit()
        return item
    except Exception as exc:
        await db.rollback()
        raise _err(exc) from exc


@router.post("/installations/{installation_id}/revoke", response_model=EmployeeMarketplaceInstallationRead)
async def revoke(
    installation_id: UUID,
    ctx: TenantContext = Depends(require_permission("employee_marketplace.revoke")),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    try:
        item = await revoke_package(
            db,
            buyer_tenant_id=ctx.tenant_id,
            installation_id=installation_id,
            actor_id=ctx.user_id,
        )
        await db.commit()
        return item
    except Exception as exc:
        await db.rollback()
        raise _err(exc) from exc
