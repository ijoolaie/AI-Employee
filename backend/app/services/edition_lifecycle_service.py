"""Lifecycle controls for vendor -> reseller -> customer tenants.

Lifecycle changes are intentionally non-destructive: deprovisioning disables
access and retains tenant data so backup/retention workflows can be added
without making the control-plane action irreversible.
"""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User
from app.services.edition_service import assert_direct_child, record_audit

STATUS_ACTIVE = "active"
STATUS_SUSPENDED = "suspended"
STATUS_DEPROVISIONED = "deprovisioned"


def validate_transition(current: str, target: str) -> None:
    allowed = {
        STATUS_ACTIVE: {STATUS_SUSPENDED, STATUS_DEPROVISIONED},
        STATUS_SUSPENDED: {STATUS_ACTIVE, STATUS_DEPROVISIONED},
        STATUS_DEPROVISIONED: set(),
    }

    if target not in allowed.get(current, set()):
        raise HTTPException(
            status_code=409,
            detail=f"Invalid tenant lifecycle transition: {current} -> {target}",
        )


def validate_deprovision_children(children: list[Tenant]) -> None:
    active_children = [
        child for child in children if child.status != STATUS_DEPROVISIONED
    ]

    if active_children:
        raise HTTPException(
            status_code=409,
            detail="Tenant cannot be deprovisioned while child tenants remain active",
        )


async def transition_tenant_status(
    db: AsyncSession,
    *,
    tenant: Tenant,
    target_status: str,
    actor_id: UUID | None,
    audit_tenant_id: UUID | None = None,
    audit_metadata: dict | None = None,
) -> Tenant:
    """Apply a validated lifecycle transition without deleting tenant data."""

    previous_status = tenant.status
    validate_transition(previous_status, target_status)

    if target_status == STATUS_DEPROVISIONED:
        children = list(
            (
                await db.execute(
                    select(Tenant).where(Tenant.parent_tenant_id == tenant.id)
                )
            )
            .scalars()
            .all()
        )

        validate_deprovision_children(children)

        users = list(
            (
                await db.execute(
                    select(User).where(User.tenant_id == tenant.id)
                )
            )
            .scalars()
            .all()
        )

        for user in users:
            user.is_active = False

    tenant.status = target_status
    await db.flush()

    metadata = {
        "tenant_id": str(tenant.id),
        "tenant_kind": tenant.tenant_kind,
        "previous_status": previous_status,
        "target_status": target_status,
    }

    if audit_metadata:
        metadata.update(audit_metadata)

    await record_audit(
        db,
        tenant_id=audit_tenant_id or tenant.id,
        actor_id=actor_id,
        action=f"edition.{target_status}",
        resource_type="tenant",
        resource_id=str(tenant.id),
        metadata=metadata,
    )

    await db.refresh(tenant)

    return tenant


async def set_child_tenant_status(
    db: AsyncSession,
    *,
    parent: Tenant,
    child_id: UUID,
    expected_kind: str,
    target_status: str,
    actor_id: UUID | None,
) -> Tenant:
    child = (
        await db.execute(
            select(Tenant).where(Tenant.id == child_id)
        )
    ).scalar_one_or_none()

    if child is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    assert_direct_child(parent, child, expected_kind)

    return await transition_tenant_status(
        db,
        tenant=child,
        target_status=target_status,
        actor_id=actor_id,
        audit_tenant_id=parent.id,
        audit_metadata={
            "child_tenant_id": str(child.id),
            "child_kind": child.tenant_kind,
        },
    )
