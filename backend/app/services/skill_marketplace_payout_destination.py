"""Governed seller payout destination binding.

This service only binds/revokes an opaque provider destination reference. It
never contacts a payout provider and never executes a transfer.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationAppError
from app.models.skill_marketplace_payout_destination import (
    SkillMarketplacePayoutDestination,
    SkillMarketplacePayoutDestinationStatus,
)


def _validate_destination(*, provider: str, destination_ref: str) -> tuple[str, str]:
    provider_value = provider.strip().lower()
    if any(ord(char) < 32 for char in destination_ref):
        raise ValidationAppError("Payout destination reference must not contain control characters")
    destination_value = destination_ref.strip()
    if not provider_value or len(provider_value) > 40:
        raise ValidationAppError("Payout destination provider is required and must be at most 40 characters")
    if not destination_value or len(destination_value) > 255:
        raise ValidationAppError("Payout destination reference is required and must be at most 255 characters")
    return provider_value, destination_value


async def get_active_payout_destination(
    db: AsyncSession,
    *,
    seller_tenant_id: uuid.UUID,
) -> SkillMarketplacePayoutDestination | None:
    result = await db.execute(
        select(SkillMarketplacePayoutDestination).where(
            SkillMarketplacePayoutDestination.seller_tenant_id == seller_tenant_id,
            SkillMarketplacePayoutDestination.status
            == SkillMarketplacePayoutDestinationStatus.ACTIVE,
        )
    )
    return result.scalar_one_or_none()


async def bind_payout_destination(
    db: AsyncSession,
    *,
    seller_tenant_id: uuid.UUID,
    provider: str,
    destination_ref: str,
    actor_user_id: uuid.UUID,
) -> SkillMarketplacePayoutDestination:
    """Create one active binding; an existing active binding must be revoked first."""
    provider_value, destination_value = _validate_destination(
        provider=provider,
        destination_ref=destination_ref,
    )
    existing = await get_active_payout_destination(
        db, seller_tenant_id=seller_tenant_id
    )
    if existing is not None:
        raise ValidationAppError(
            "Seller already has an active payout destination; revoke it before binding another"
        )

    binding = SkillMarketplacePayoutDestination(
        seller_tenant_id=seller_tenant_id,
        provider=provider_value,
        destination_ref=destination_value,
        status=SkillMarketplacePayoutDestinationStatus.ACTIVE,
        created_by_user_id=actor_user_id,
    )
    db.add(binding)
    await db.flush()
    return binding


async def revoke_payout_destination(
    db: AsyncSession,
    *,
    seller_tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID,
) -> SkillMarketplacePayoutDestination:
    binding = await get_active_payout_destination(
        db, seller_tenant_id=seller_tenant_id
    )
    if binding is None:
        raise ValidationAppError("Seller has no active payout destination")

    binding.status = SkillMarketplacePayoutDestinationStatus.REVOKED
    binding.revoked_by_user_id = actor_user_id
    binding.revoked_at = datetime.now(timezone.utc)
    await db.flush()
    return binding
