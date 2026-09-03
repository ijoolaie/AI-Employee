"""Phase 13.3 authorized Agent Team execution endpoint."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.deps import DbSession, TeamExecuteContext
from app.services.audit_service import record
from app.services.team_execution import TeamExecutionError, TeamExecutionService

router = APIRouter(prefix="/team-executions", tags=["team-executions"])


class TeamExecutionCreate(BaseModel):
    installation_id: UUID
    input_data: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1, max_length=255)
    title: str | None = Field(default=None, max_length=255)
    correlation_id: str | None = Field(default=None, max_length=128)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def execute_team(
    payload: TeamExecutionCreate,
    ctx: TeamExecuteContext,
    db: DbSession,
):
    try:
        result = await TeamExecutionService(db).execute(
            tenant_id=ctx.tenant_id,
            installation_id=payload.installation_id,
            input_data=payload.input_data,
            actor_id=ctx.user_id,
            idempotency_key=payload.idempotency_key,
            title=payload.title,
            correlation_id=payload.correlation_id,
        )
        await record(
            db,
            action="team_execution.dispatched",
            actor_type="user",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            resource_type="work_item",
            resource_id=UUID(result["work_item_id"]),
            request_id=result["correlation_id"],
            metadata={
                "team_installation_id": result["team_installation_id"],
                "team_version_id": result["team_version_id"],
                "member_count": len(result["members"]),
            },
        )
        await db.commit()
    except TeamExecutionError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return result
