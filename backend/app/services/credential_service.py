from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.security import decrypt_secret, encrypt_secret
from app.models.credential import Credential
from app.services import audit_service
from app.services.agent_governance import current_agent_execution_context
from app.services.agent_policy_engine import PolicyRequest, assert_authorized


async def store_credential(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    provider: str,
    name: str,
    secret: str,
    expires_at=None,
) -> Credential:
    if not secret:
        raise ValidationAppError("Credential secret cannot be empty")
    credential = Credential(
        tenant_id=tenant_id,
        provider=provider,
        name=name,
        ciphertext=encrypt_secret(secret),
        status="active",
        active=True,
        expires_at=expires_at,
    )
    db.add(credential)
    await db.flush()
    await audit_service.record(
        db,
        action="credential.created",
        actor_type="system",
        tenant_id=tenant_id,
        resource_type="credential",
        resource_id=credential.id,
        metadata={"provider": provider, "name": name},
    )
    return credential


async def resolve_credential(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    credential_id: uuid.UUID,
    agent_instance_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    tool_name: str = "credential.vault",
) -> str:
    credential = (
        await db.execute(
            select(Credential).where(
                Credential.id == credential_id,
                Credential.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if credential is None:
        raise NotFoundError("Credential not found for tenant")
    now = datetime.now(timezone.utc)
    if not credential.active or credential.status != "active" or credential.revoked_at is not None:
        raise ValidationAppError("Credential has been revoked")
    if credential.expires_at is not None and credential.expires_at <= now:
        raise ValidationAppError("Credential has expired")

    context = current_agent_execution_context()
    if context is not None:
        ctx_tenant, ctx_agent, ctx_run, _employee_id, _version_id = context
        if ctx_tenant != tenant_id or (agent_instance_id is not None and ctx_agent != agent_instance_id) or (run_id is not None and ctx_run != run_id):
            raise ValidationAppError("Credential execution context mismatch")
        agent_instance_id = ctx_agent
        run_id = ctx_run
        await assert_authorized(
            db,
            PolicyRequest(
                tenant_id=tenant_id,
                agent_instance_id=agent_instance_id,
                action="credential.read",
                tool_name=tool_name,
                required_permission="credential.read",
                resource_type="credential",
                resource_id=str(credential.id),
                run_id=run_id,
                context={"credential_provider": credential.provider},
            ),
        )
    elif agent_instance_id is not None or run_id is not None:
        raise ValidationAppError("Agent credential access requires governed execution context")

    credential.last_used_at = now
    await audit_service.record(
        db,
        action="credential.used",
        actor_type="agent" if context is not None else "system",
        tenant_id=tenant_id,
        resource_type="credential",
        resource_id=credential.id,
        metadata={"provider": credential.provider, "agent_instance_id": str(agent_instance_id) if agent_instance_id else None, "run_id": str(run_id) if run_id else None},
    )
    return decrypt_secret(credential.ciphertext)


async def revoke_credential(db: AsyncSession, *, tenant_id: uuid.UUID, credential_id: uuid.UUID) -> Credential:
    credential = (
        await db.execute(
            select(Credential).where(Credential.id == credential_id, Credential.tenant_id == tenant_id).with_for_update()
        )
    ).scalar_one_or_none()
    if credential is None:
        raise NotFoundError("Credential not found for tenant")
    if credential.active:
        credential.active = False
        credential.status = "revoked"
        credential.revoked_at = datetime.now(timezone.utc)
        await audit_service.record(
            db,
            action="credential.revoked",
            actor_type="system",
            tenant_id=tenant_id,
            resource_type="credential",
            resource_id=credential.id,
            metadata={"provider": credential.provider},
        )
    return credential


def credential_ref(credential: Credential) -> str:
    return f"cred:{credential.id}"
