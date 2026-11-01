"""Commercial license issuance/revocation within edition boundaries."""
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import DbSession
from app.core.edition_deps import ResellerAdminContext, VendorAdminContext
from app.models.tenant import Tenant
from app.models.license import CommercialLicense
from app.schemas.common import APIResponse
from app.schemas.edition import LicenseIssueRequest, LicenseListResponse, LicenseResponse, LicenseRevokeRequest
from app.services import edition_service, license_service

router = APIRouter(prefix="/edition/licenses", tags=["commercial-license"])


@router.get("/vendor", response_model=APIResponse[list[LicenseListResponse]])
async def list_vendor_licenses(ctx: VendorAdminContext, db: DbSession):
    """List only licenses issued by this vendor; never expose bearer keys."""
    rows = (await db.execute(
        select(CommercialLicense)
        .where(CommercialLicense.issuer_tenant_id == ctx.tenant_id)
        .order_by(CommercialLicense.issued_at.desc())
        .limit(200)
    )).scalars().all()
    return APIResponse(success=True, data=rows)


@router.get("/reseller", response_model=APIResponse[list[LicenseListResponse]])
async def list_reseller_licenses(ctx: ResellerAdminContext, db: DbSession):
    """List only licenses issued by this reseller; never expose bearer keys."""
    rows = (await db.execute(
        select(CommercialLicense)
        .where(CommercialLicense.issuer_tenant_id == ctx.tenant_id)
        .order_by(CommercialLicense.issued_at.desc())
        .limit(200)
    )).scalars().all()
    return APIResponse(success=True, data=rows)


@router.post("/vendor/tenants/{tenant_id}", response_model=APIResponse[LicenseResponse], status_code=201)
async def issue_vendor_tenant_license(tenant_id: UUID, payload: LicenseIssueRequest, ctx: VendorAdminContext, db: DbSession):
    """Manually issue a commercial license to any tenant in this vendor's hierarchy."""
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    row = await license_service.issue_license(
        db,
        issuer=ctx.tenant,
        tenant=tenant,
        expires_in_days=payload.expires_in_days,
        feature_codes=payload.feature_codes,
        metadata=payload.metadata,
    )
    return APIResponse(success=True, data=row)


@router.post("/vendor/resellers/{reseller_id}", response_model=APIResponse[LicenseResponse], status_code=201)
async def issue_reseller_license(reseller_id: UUID, payload: LicenseIssueRequest, ctx: VendorAdminContext, db: DbSession):
    tenant = (await db.execute(select(Tenant).where(Tenant.id == reseller_id))).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Reseller tenant not found")
    edition_service.assert_direct_child(ctx.tenant, tenant, edition_service.EDITION_RESELLER)
    row = await license_service.issue_license(db, issuer=ctx.tenant, tenant=tenant, expires_in_days=payload.expires_in_days, feature_codes=payload.feature_codes, metadata=payload.metadata)
    return APIResponse(success=True, data=row)


@router.post("/reseller/customers/{customer_id}", response_model=APIResponse[LicenseResponse], status_code=201)
async def issue_customer_license(customer_id: UUID, payload: LicenseIssueRequest, ctx: ResellerAdminContext, db: DbSession):
    tenant = (await db.execute(select(Tenant).where(Tenant.id == customer_id))).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Customer tenant not found")
    edition_service.assert_direct_child(ctx.tenant, tenant, edition_service.EDITION_CUSTOMER)
    row = await license_service.issue_license(db, issuer=ctx.tenant, tenant=tenant, expires_in_days=payload.expires_in_days, feature_codes=payload.feature_codes, metadata=payload.metadata)
    return APIResponse(success=True, data=row)


@router.post("/vendor/{license_id}/revoke", response_model=APIResponse[LicenseListResponse])
async def revoke_vendor_license(license_id: UUID, payload: LicenseRevokeRequest, ctx: VendorAdminContext, db: DbSession):
    row = await license_service.revoke_license(db, issuer=ctx.tenant, license_id=license_id, reason=payload.reason)
    return APIResponse(success=True, data=row)


@router.post("/reseller/{license_id}/revoke", response_model=APIResponse[LicenseListResponse])
async def revoke_reseller_license(license_id: UUID, payload: LicenseRevokeRequest, ctx: ResellerAdminContext, db: DbSession):
    row = await license_service.revoke_license(db, issuer=ctx.tenant, license_id=license_id, reason=payload.reason)
    return APIResponse(success=True, data=row)
