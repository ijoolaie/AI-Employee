"""API key issuance, verification and lifecycle management."""
import hashlib
import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey

KEY_PREFIX = "aiep_live_"


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _new_secret() -> str:
    return KEY_PREFIX + secrets.token_urlsafe(32)


async def create_key(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    name: str,
    expires_at,
    scopes: list[str],
):
    secret = _new_secret()
    row = APIKey(
        tenant_id=tenant_id,
        created_by=user_id,
        name=name,
        key_prefix=secret[:20],
        key_hash=_digest(secret),
        expires_at=expires_at,
        scopes=sorted(set(scopes)),
    )
    db.add(row)
    await db.flush()
    return row, secret


async def list_keys(db: AsyncSession, *, tenant_id: UUID):
    result = await db.execute(
        select(APIKey).where(APIKey.tenant_id == tenant_id).order_by(APIKey.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_key(db: AsyncSession, *, tenant_id: UUID, key_id: UUID):
    result = await db.execute(select(APIKey).where(APIKey.id == key_id, APIKey.tenant_id == tenant_id))
    row = result.scalar_one_or_none()
    if row is None:
        return None
    if row.is_active:
        row.is_active = False
        row.revoked_at = datetime.now(timezone.utc)
    await db.flush()
    return row


async def verify_key(db: AsyncSession, secret: str):
    digest = _digest(secret)
    result = await db.execute(select(APIKey).where(APIKey.key_hash == digest))
    row = result.scalar_one_or_none()
    if row is None or not row.is_active:
        return None
    now = datetime.now(timezone.utc)
    if row.expires_at and row.expires_at <= now:
        row.is_active = False
        await db.flush()
        return None
    row.last_used_at = now
    await db.flush()
    return row
