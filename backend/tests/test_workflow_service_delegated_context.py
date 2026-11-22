from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest
from fastapi import HTTPException

from app.services import portal_access_service, run_service, workflow_service


@pytest.mark.asyncio
async def test_workflow_run_revalidates_persisted_actor_and_grant(monkeypatch):
    customer_tenant_id = uuid.uuid4()
    actor_tenant_id = uuid.uuid4()
    actor_user_id = uuid.uuid4()
    grant_id = uuid.uuid4()
    run = SimpleNamespace(
        tenant_id=customer_tenant_id,
        actor_tenant_id=actor_tenant_id,
        created_by=actor_user_id,
        portal_access_grant_id=grant_id,
        status="pending",
        error=None,
        completed_at=None,
        execution_lease_id=uuid.uuid4(),
        execution_lease_expires_at=object(),
        execution_heartbeat_at=object(),
    )
    validate = AsyncMock()
    db = object()
    monkeypatch.setattr(portal_access_service, "validate_portal_access_grant", validate)
    monkeypatch.setattr(run_service, "actor_has_tenant_permission", AsyncMock(return_value=True))

    assert await workflow_service.validate_workflow_run_portal_context(db, run=run) is True
    validate.assert_awaited_once_with(
        db,
        actor_user_id=actor_user_id,
        actor_tenant_id=actor_tenant_id,
        target_tenant_id=customer_tenant_id,
        grant_id=grant_id,
    )
    assert run.status == "pending"


@pytest.mark.asyncio
async def test_workflow_run_revocation_fails_closed_and_releases_lease(monkeypatch):
    run = SimpleNamespace(
        tenant_id=uuid.uuid4(),
        actor_tenant_id=uuid.uuid4(),
        created_by=uuid.uuid4(),
        portal_access_grant_id=uuid.uuid4(),
        status="running",
        error=None,
        completed_at=None,
        execution_lease_id=uuid.uuid4(),
        execution_lease_expires_at=object(),
        execution_heartbeat_at=object(),
    )
    db = SimpleNamespace(flush=AsyncMock())

    async def _revoked(*_args, **_kwargs):
        raise HTTPException(status_code=403, detail="Active portal access grant required")

    monkeypatch.setattr(portal_access_service, "validate_portal_access_grant", _revoked)

    assert await workflow_service.validate_workflow_run_portal_context(db, run=run) is False
    assert run.status == "failed"
    assert run.error["code"] == "DELEGATED_PORTAL_CONTEXT_INVALID"
    assert "Active portal access grant required" in run.error["message"]
    assert run.completed_at is not None
    assert run.execution_lease_id is None
    assert run.execution_lease_expires_at is None
    assert run.execution_heartbeat_at is None
    db.flush.assert_awaited_once()


def test_workflow_child_runs_inherit_parent_actor_and_grant_provenance():
    source = (Path(__file__).parents[1] / "app/services/workflow_service.py").read_text()
    assert source.count("actor_tenant_id=parent.actor_tenant_id") == 1
    assert source.count("portal_access_grant_id=parent.portal_access_grant_id") == 1
    assert source.count("actor_tenant_id=run.actor_tenant_id") == 3
    assert source.count("portal_access_grant_id=run.portal_access_grant_id") == 1




@pytest.mark.asyncio
async def test_workflow_run_without_grant_rejects_cross_tenant_actor():
    run = SimpleNamespace(
        tenant_id=uuid.uuid4(),
        actor_tenant_id=uuid.uuid4(),
        created_by=uuid.uuid4(),
        portal_access_grant_id=None,
        status="pending",
        error=None,
        completed_at=None,
        execution_lease_id=None,
        execution_lease_expires_at=None,
        execution_heartbeat_at=None,
    )
    db = SimpleNamespace(flush=AsyncMock())

    assert await workflow_service.validate_workflow_run_portal_context(db, run=run) is False
    assert run.status == "failed"
    assert run.error["code"] == "DELEGATED_PORTAL_CONTEXT_INVALID"
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_workflow_run_without_grant_requires_active_creator_membership():
    tenant_id = uuid.uuid4()
    run = SimpleNamespace(
        tenant_id=tenant_id,
        actor_tenant_id=tenant_id,
        created_by=uuid.uuid4(),
        portal_access_grant_id=None,
        status="pending",
        error=None,
        completed_at=None,
        execution_lease_id=None,
        execution_lease_expires_at=None,
        execution_heartbeat_at=None,
    )
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None)),
        flush=AsyncMock(),
    )

    assert await workflow_service.validate_workflow_run_portal_context(db, run=run) is False
    assert run.status == "failed"
    assert "not an active member" in run.error["message"]
    db.execute.assert_awaited_once()
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_workflow_run_system_actor_without_creator_uses_effective_tenant():
    tenant_id = uuid.uuid4()
    run = SimpleNamespace(
        tenant_id=tenant_id,
        actor_tenant_id=tenant_id,
        created_by=None,
        portal_access_grant_id=None,
        status="pending",
        error=None,
        completed_at=None,
        execution_lease_id=None,
        execution_lease_expires_at=None,
        execution_heartbeat_at=None,
    )

    assert await workflow_service.validate_workflow_run_portal_context(object(), run=run) is True
    assert run.status == "pending"


def test_workflow_parallel_branch_revalidates_parent_delegation():
    source = (Path(__file__).parents[1] / "app/services/workflow_service.py").read_text()
    branch = source[source.index("async def _execute_parallel_branch"):source.index("async def execute_workflow")]
    assert "validate_workflow_run_portal_context(db, run=parent)" in branch



@pytest.mark.asyncio
async def test_workflow_run_rejects_revoked_workflow_execute_permission(monkeypatch):
    run = SimpleNamespace(
        tenant_id=uuid.uuid4(),
        actor_tenant_id=uuid.uuid4(),
        created_by=uuid.uuid4(),
        portal_access_grant_id=uuid.uuid4(),
        status="pending",
        error=None,
        completed_at=None,
        execution_lease_id=None,
        execution_lease_expires_at=None,
        execution_heartbeat_at=None,
    )
    db = SimpleNamespace(flush=AsyncMock())

    async def _grant_active(*_args, **_kwargs):
        return None

    monkeypatch.setattr(portal_access_service, "validate_portal_access_grant", _grant_active)
    monkeypatch.setattr(run_service, "actor_has_tenant_permission", AsyncMock(return_value=False))

    assert await workflow_service.validate_workflow_run_portal_context(db, run=run) is False
    assert run.status == "failed"
    assert "workflow.execute permission" in run.error["message"]
    db.flush.assert_awaited_once()




def test_workflow_actor_provenance_columns_belong_to_workflow_run_model():
    from app.models.workflow import Workflow, WorkflowRun

    assert "actor_tenant_id" not in Workflow.__table__.columns
    assert "portal_access_grant_id" not in Workflow.__table__.columns
    assert "actor_tenant_id" in WorkflowRun.__table__.columns
    assert "portal_access_grant_id" in WorkflowRun.__table__.columns
