"""Test Center worker execution dispatch boundary."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import RunExecuteContext
from app.models.test_run import TestRun, TestRunStatus
from app.services.audit_service import record
from app.workers.test_center_worker import execute_run_task

router = APIRouter(prefix="/test-center", tags=["test-center"])


class TestRunExecutionDispatch(BaseModel):
    run_id: UUID
    task_id: str
    status: str


@router.post("/runs/{run_id}/execute", response_model=TestRunExecutionDispatch, status_code=status.HTTP_202_ACCEPTED)
async def execute_run(run_id: UUID, ctx: RunExecuteContext, db: AsyncSession = Depends(get_db)):
    run = (
        await db.execute(
            select(TestRun).where(TestRun.id == run_id, TestRun.tenant_id == ctx.tenant_id)
        )
    ).scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="test run not found")
    if run.status is not TestRunStatus.QUEUED:
        raise HTTPException(status_code=409, detail="only queued test runs can be dispatched")

    try:
        task = execute_run_task.delay(str(run.id))
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=503, detail="test run worker dispatch failed") from exc

    await record(
        db,
        action="test_run.dispatched",
        actor_type="user",
        actor_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        resource_type="test_run",
        resource_id=run.id,
        metadata={"correlation_id": str(run.correlation_id), "source": "api", "task_id": task.id},
    )
    await db.commit()
    return TestRunExecutionDispatch(run_id=run.id, task_id=task.id, status="dispatched")
