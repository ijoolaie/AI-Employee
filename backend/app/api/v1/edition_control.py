"""Vendor/reseller/customer runtime control-plane boundaries."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import DbSession
from app.core.edition_deps import CustomerAdminContext, ResellerAdminContext, VendorAdminContext
from app.models.tenant import Tenant
from app.models.tenant_entitlement import TenantEntitlement
from app.schemas.common import APIResponse
from app.schemas.edition import (
    ChildTenantProvisionRequest,
    EntitlementDelegationRequest,
    EntitlementResponse,
    SupportEscalationRequest,
    SupportEscalationResponse,
    TenantSummary,
)
from app.services import edition_service

router = APIRouter(prefix="/edition", tags=["edition-control"])


@router.get("/vendor/resellers", response_model=APIResponse[list[TenantSummary]])
async def list_resellers(ctx: VendorAdminContext, db: DbSession):
    rows = (await db.execute(select(Tenant).where(Tenant.parent_tenant_id == ctx.tenant_id, Tenant.tenant_kind == edition_service.EDITION_RESELLER).order_by(Tenant.created_at))).scalars().all()
    return APIResponse(success=True, data=rows)


@router.post("/vendor/resellers", response_model=APIResponse[TenantSummary], status_code=201)
async def create_reseller(payload: ChildTenantProvisionRequest, ctx: VendorAdminContext, db: DbSession):
    tenant, _ = await edition_service.provision_child_tenant(
        db,
        parent=ctx.tenant,
        name=payload.name,
        slug=payload.slug,
        admin_email=payload.admin_email,
        admin_password=payload.admin_password,
        full_name=payload.full_name,
        kind=edition_service.EDITION_RESELLER,
        vendor_release_tag=payload.vendor_release_tag,
        delivery_revision=payload.delivery_revision,
    )
    return APIResponse(success=True, data=tenant)


@router.get("/reseller/customers", response_model=APIResponse[list[TenantSummary]])
async def list_customers(ctx: ResellerAdminContext, db: DbSession):
    rows = (await db.execute(select(Tenant).where(Tenant.parent_tenant_id == ctx.tenant_id, Tenant.tenant_kind == edition_service.EDITION_CUSTOMER).order_by(Tenant.created_at))).scalars().all()
    return APIResponse(success=True, data=rows)


@router.post("/reseller/customers", response_model=APIResponse[TenantSummary], status_code=201)
async def create_customer(payload: ChildTenantProvisionRequest, ctx: ResellerAdminContext, db: DbSession):
    tenant, _ = await edition_service.provision_child_tenant(
        db,
        parent=ctx.tenant,
        name=payload.name,
        slug=payload.slug,
        admin_email=payload.admin_email,
        admin_password=payload.admin_password,
        full_name=payload.full_name,
        kind=edition_service.EDITION_CUSTOMER,
        vendor_release_tag=payload.vendor_release_tag,
        delivery_revision=payload.delivery_revision,
    )
    return APIResponse(success=True, data=tenant)


@router.post("/reseller/customers/{customer_id}/entitlements", response_model=APIResponse[EntitlementResponse])
async def delegate_customer_entitlement(customer_id: UUID, payload: EntitlementDelegationRequest, ctx: ResellerAdminContext, db: DbSession):
    child = (await db.execute(select(Tenant).where(Tenant.id == customer_id))).scalar_one_or_none()
    if child is None:
        raise HTTPException(status_code=404, detail="Customer tenant not found")
    row = await edition_service.delegate_entitlement(db, parent=ctx.tenant, child=child, feature_code=payload.feature_code, quota_limit=payload.quota_limit)
    return APIResponse(success=True, data=row)


@router.post("/support/escalations", response_model=APIResponse[SupportEscalationResponse], status_code=201)
async def create_escalation(payload: SupportEscalationRequest, ctx: CustomerAdminContext, db: DbSession):
    row = await edition_service.create_support_escalation(
        db,
        from_tenant=ctx.tenant,
        opened_by=ctx.user_id,
        subject=payload.subject,
        description=payload.description,
    )
    return APIResponse(success=True, data=row)


@router.post("/reseller/support/escalations", response_model=APIResponse[SupportEscalationResponse], status_code=201)
async def create_reseller_escalation(payload: SupportEscalationRequest, ctx: ResellerAdminContext, db: DbSession):
    row = await edition_service.create_support_escalation(
        db,
        from_tenant=ctx.tenant,
        opened_by=ctx.user_id,
        subject=payload.subject,
        description=payload.description,
    )
    return APIResponse(success=True, data=row)


@router.get("/customer/{customer_id}/entitlements", response_model=APIResponse[list[EntitlementResponse]])
async def list_customer_entitlements(customer_id: UUID, ctx: ResellerAdminContext, db: DbSession):
    child = (await db.execute(select(Tenant).where(Tenant.id == customer_id))).scalar_one_or_none()
    if child is None:
        raise HTTPException(status_code=404, detail="Customer tenant not found")
    edition_service.assert_direct_child(ctx.tenant, child, edition_service.EDITION_CUSTOMER)
    rows = (await db.execute(select(TenantEntitlement).where(TenantEntitlement.tenant_id == child.id).order_by(TenantEntitlement.feature_code))).scalars().all()
    return APIResponse(success=True, data=rows)
