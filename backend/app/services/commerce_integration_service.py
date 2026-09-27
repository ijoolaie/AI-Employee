import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.commerce_integration import CommerceIntegration
from app.services import audit_service
from app.services.credential_service import credential_ref, store_credential

SECRET_KEYS = {"api_key", "access_token", "client_secret", "password", "token"}
COMMERCE_INTEGRATION_PROVIDER_INDEX_NAME = "uq_commerce_integrations_tenant_provider"


def _redact(config: dict) -> dict:
    return {
        k: ("••••••••" if k.lower() in SECRET_KEYS or k == "credential_refs" else v)
        for k, v in (config or {}).items()
    }


async def list_integrations(db: AsyncSession, tenant_id: uuid.UUID):
    return list(
        (
            await db.execute(
                select(CommerceIntegration)
                .where(CommerceIntegration.tenant_id == tenant_id)
                .order_by(CommerceIntegration.created_at.desc())
            )
        )
        .scalars()
        .all()
    )


async def _extract_credentials(
    db: AsyncSession, *, tenant_id: uuid.UUID, provider: str, config: dict
) -> dict:
    safe = dict(config or {})
    refs = dict(safe.get("credential_refs") or {})
    for key in list(safe):
        if key.lower() not in SECRET_KEYS:
            continue
        value = safe.pop(key)
        if value:
            credential = await store_credential(
                db,
                tenant_id=tenant_id,
                provider=provider,
                name=f"{provider}:{key}",
                secret=str(value),
            )
            refs[key] = credential_ref(credential)
    if refs:
        safe["credential_refs"] = refs
    return safe


async def create_integration(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    provider: str,
    name: str,
    config: dict,
    actor_id: uuid.UUID | None = None,
):
    existing = (
        await db.execute(
            select(CommerceIntegration).where(
                CommerceIntegration.tenant_id == tenant_id,
                CommerceIntegration.provider == provider,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError(f"{provider} integration already exists for this tenant")

    try:
        async with db.begin_nested():
            safe_config = await _extract_credentials(
                db, tenant_id=tenant_id, provider=provider, config=config
            )
            integration = CommerceIntegration(
                tenant_id=tenant_id,
                provider=provider,
                name=name,
                config=safe_config,
                status="configured",
                is_active=False,
            )
            db.add(integration)
            await db.flush()
    except IntegrityError as exc:
        constraint_name = getattr(exc.orig, "constraint_name", None)
        if constraint_name != COMMERCE_INTEGRATION_PROVIDER_INDEX_NAME:
            raise
        raise ConflictError(
            f"{provider} integration already exists for this tenant"
        ) from exc

    await audit_service.record(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="commerce.integration.created",
        resource_type="commerce_integration",
        resource_id=integration.id,
        metadata={"provider": provider, "name": name},
    )
    await db.refresh(integration)
    return integration


def public_config(integration):
    return {**integration.__dict__, "config": _redact(integration.config)}
