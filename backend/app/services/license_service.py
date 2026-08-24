"""Commercial license issuance, revocation and execution-boundary checks."""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.license import CommercialLicense
from app.models.tenant import Tenant
from app.models.tenant_entitlement import TenantEntitlement
from app.services import edition_service


def _license_key() -> str:
    return "LIC-" + secrets.token_urlsafe(36).replace("-", "_")[:64]


async def issue_license(
    db: AsyncSession,
    *,
    issuer: Tenant,
    tenant: Tenant,
    expires_in_days: int | None = None,
    feature_codes: list[str] | None = None,
    metadata: dict | None = None,
) -> CommercialLicense:
    expected_kind = (
        edition_service.EDITION_RESELLER
        if issuer.tenant_kind == edition_service.EDITION_VENDOR
        else edition_service.EDITION_CUSTOMER
    )
    edition_service.assert_direct_child(issuer, tenant, expected_kind)
    existing = (
        await db.execute(
            select(CommercialLicense).where(
                CommercialLicense.tenant_id == tenant.id,
                CommercialLicense.status == "active",
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("An active commercial license already exists")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=expires_in_days) if expires_in_days else None
    normalized_features = sorted(set(feature_codes or []))
    if not normalized_features:
        raise ConflictError("Commercial licenses must declare at least one feature code")

    license_row = CommercialLicense(
        license_key=_license_key(),
        issuer_tenant_id=issuer.id,
        tenant_id=tenant.id,
        edition=tenant.tenant_kind,
        status="active",
        issued_at=now,
        expires_at=expires_at,
        feature_codes=normalized_features,
        license_metadata=metadata or {},
    )
    db.add(license_row)
    await db.flush()
    await edition_service.record_audit(
        db,
        tenant_id=issuer.id,
        actor_id=None,
        action="license.issued",
        resource_type="commercial_license",
        resource_id=str(license_row.id),
        metadata={
            "tenant_id": str(tenant.id),
            "edition": tenant.tenant_kind,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "feature_count": len(normalized_features),
        },
    )
    await db.refresh(license_row)
    return license_row


async def revoke_license(
    db: AsyncSession,
    *,
    issuer: Tenant,
    license_id: uuid.UUID,
    reason: str,
) -> CommercialLicense:
    license_row = (
        await db.execute(select(CommercialLicense).where(CommercialLicense.id == license_id))
    ).scalar_one_or_none()
    if license_row is None:
        raise NotFoundError("Commercial license not found")
    if license_row.issuer_tenant_id != issuer.id:
        raise ConflictError("License issuer boundary violation")
    if license_row.status == "revoked":
        return license_row
    license_row.status = "revoked"
    license_row.revoked_at = datetime.now(timezone.utc)
    license_row.revocation_reason = reason
    await db.flush()
    await edition_service.record_audit(
        db,
        tenant_id=issuer.id,
        actor_id=None,
        action="license.revoked",
        resource_type="commercial_license",
        resource_id=str(license_row.id),
        metadata={"tenant_id": str(license_row.tenant_id), "reason": reason},
    )
    await db.refresh(license_row)
    return license_row


async def get_active_license(
    db: AsyncSession, *, tenant_id: uuid.UUID
) -> CommercialLicense | None:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(CommercialLicense)
        .where(
            CommercialLicense.tenant_id == tenant_id,
            CommercialLicense.status == "active",
        )
        .order_by(CommercialLicense.issued_at.desc())
    )
    row = result.scalars().first()
    if row and row.expires_at and row.expires_at <= now:
        row.status = "expired"
        await db.flush()
        return None
    return row


async def assert_feature_entitlement(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    feature_code: str,
) -> CommercialLicense:
    """Authorize one commercial feature at execution time.

    Explicit feature codes are mandatory for newly issued licenses. Only the
    migration-created ``grandfathered`` legacy licenses may use an empty list,
    preserving existing tenants without making an accidentally empty new
    license equivalent to unlimited access.
    """
    license_row = await assert_execution_license(db, tenant_id=tenant_id)
    licensed_features = set(license_row.feature_codes or [])
    grandfathered = bool((license_row.license_metadata or {}).get("grandfathered"))
    if not licensed_features and not grandfathered:
        raise ConflictError("Commercial license has no authorized features")
    if licensed_features and feature_code not in licensed_features:
        raise ConflictError(f"Commercial license does not include feature: {feature_code}")

    result = await db.execute(
        select(TenantEntitlement).where(
            TenantEntitlement.tenant_id == tenant_id,
            TenantEntitlement.feature_code == feature_code,
        )
    )
    entitlement = result.scalar_one_or_none()
    if entitlement is not None and not entitlement.is_enabled:
        raise ConflictError(f"Tenant entitlement is disabled for feature: {feature_code}")
    return license_row


async def assert_execution_license(
    db: AsyncSession, *, tenant_id: uuid.UUID
) -> CommercialLicense:
    license_row = await get_active_license(db, tenant_id=tenant_id)
    if license_row is None:
        raise ConflictError("Commercial license is missing, expired, or revoked")
    return license_row
