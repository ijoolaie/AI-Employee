"""Governed Agent-to-Agent delegation API."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_context, require_permission
from app.models.agent_delegation import AgentDelegation
from app.services import audit_service
from app.services.agent_delegation_service import create_delegated_work_item

router = APIRouter(prefix="/agent-delegations", tags=["agent-delegations"])


class AgentDelegationRequest(BaseModel):
    delegator_agent_instance_id: UUID
    delegate_agent_instance_id: UUID
    scopes: dict = Field(default_factory=dict)
    expires_at: datetime
    max_chain_depth: int = Field(default=3, ge=1, le=3)
    title: str | None = None
    description: str | None = None
    context: dict | None = None
    artifacts: list[dict] | None = None


class AgentDelegationResponse(BaseModel):
    delegation_id: UUID
    work_item_id: UUID
    tenant_id: UUID
    delegate_agent_instance_id: UUID
    chain_depth: int
    expires_at: datetime
    scopes: dict


@router.post(
    "/{source_work_item_id}",
    response_model=AgentDelegationResponse,
    dependencies=[Depends(require_permission("run.execute"))],
)
async def delegate_agent(
    source_work_item_id: UUID,
    payload: AgentDelegationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_context),
):
    try:
        child = await create_delegated_work_item(
            db,
            source_work_item_id=source_work_item_id,
            delegator_agent_instance_id=payload.delegator_agent_instance_id,
            delegate_agent_instance_id=payload.delegate_agent_instance_id,
            scopes=payload.scopes,
            expires_at=payload.expires_at,
            title=payload.title,
            description=payload.description,
            context=payload.context,
            artifacts=payload.artifacts,
            max_chain_depth=payload.max_chain_depth,
        )
        delegation_id = UUID(str((child.policy_context or {})["delegation_id"]))
        await audit_service.record(
            db,
            action="agent.delegation.requested",
            actor_type="user",
            actor_id=current_user.user_id,
            tenant_id=current_user.tenant_id,
            resource_type="agent_delegation",
            resource_id=delegation_id,
            metadata={"source_work_item_id": str(source_work_item_id), "delegate_agent_instance_id": str(payload.delegate_agent_instance_id)},
        )
        await db.commit()
        delegation = await db.get(AgentDelegation, delegation_id)
        if delegation is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="delegation was not persisted")
        return AgentDelegationResponse(
            delegation_id=delegation_id,
            work_item_id=child.id,
            tenant_id=child.tenant_id,
            delegate_agent_instance_id=child.executor_id,
            chain_depth=delegation.chain_depth,
            expires_at=delegation.expires_at,
            scopes=delegation.scopes,
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
