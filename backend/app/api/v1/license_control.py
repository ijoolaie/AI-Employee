"""Commercial license issuance/revocation within edition boundaries."""
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import DbSession
from app.core.edition_deps import ResellerAdminContext, VendorAdminContext
from app.models.license import CommercialLicense
from app.models.tenant import Tenant
from app.schemas.common import APIResponse
from app.schemas.edition import LicenseIssueRequest, LicenseResponse, LicenseRevokeRequest
from app.services import edition_service, license_service

router = APIRouter(prefix="/edition/licenses", tags=["commercial-license"])


@router.post("/vendor/resellers/{reseller_id}", response_model=APIResponse[LicenseResponse], status_code=201)
async def issue_reseller_license(reseller_id: UUID, payload: LicenseIssueRequest, ctx: VendorAdminContext, db: DbSession):
    tenant = (await db.execute(select(Tenant).where(Tenant.id == reseller_id))).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Reseller tenant not found")
    edition_service.assert_direct_child(ctx.tenant, tenant, edition_service.EDITION_RESELLER)
    row = await license_service.issue_license(
        db, issuer=ctx.tenant, tenant=tenant,
        expires_in_days=payload.expires_in_days,
        feature_codes=payload.feature_codes,
        metadata=payload.metadata,
    )
    return APIResponse(success=True, data=row)


@router.post("/reseller/customers/{customer_id}", response_model=APIResponse[LicenseResponse], status_code=201)
async def issue_customer_license(customer_id: UUID, payload: LicenseIssueRequest, ctx: ResellerAdminContext, db: DbSession):
    tenant = (await db.execute(select(Tenant).where(Tenant.id == customer_id))).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Customer tenant not found")
    edition_service.assert_direct_child(ctx.tenant, tenant, edition_service.EDITION_CUSTOMER)
    row = await license_service.issue_license(
        db, issuer=ctx.tenant, tenant=tenant,
        expires_in_days=payload.expires_in_days,
        feature_codes=payload.feature_codes,
        metadata=payload.metadata,
    )
    return APIResponse(success=True, data=row)


@router.post("/{license_id}/revoke", response_model=APIResponse[LicenseResponse])
async def revoke_license(license_id: UUID, payload: LicenseRevokeRequest, ctx: VendorAdminContext, db: DbSession):
    row = await license_service.revoke_license(db, issuer=ctx.tenant, license_id=license_id, reason=payload.reason)
    return APIResponse(success=True, data=row)
