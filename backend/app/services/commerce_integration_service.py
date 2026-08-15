import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.commerce_integration import CommerceIntegration

SECRET_KEYS = {"api_key", "access_token", "client_secret", "password", "token"}

def _redact(config: dict) -> dict:
    return {k: ("••••••••" if k.lower() in SECRET_KEYS else v) for k, v in (config or {}).items()}

async def list_integrations(db: AsyncSession, tenant_id: uuid.UUID):
    return list((await db.execute(select(CommerceIntegration).where(CommerceIntegration.tenant_id == tenant_id).order_by(CommerceIntegration.created_at.desc()))).scalars().all())

async def create_integration(db: AsyncSession, tenant_id: uuid.UUID, provider: str, name: str, config: dict):
    integration = CommerceIntegration(tenant_id=tenant_id, provider=provider, name=name, config=config or {}, status="configured", is_active=False)
    db.add(integration); await db.flush(); await db.refresh(integration)
    return integration

def public_config(integration):
    return {**integration.__dict__, "config": _redact(integration.config)}
