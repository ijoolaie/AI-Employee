import uuid

import pytest

from app.core.exceptions import ValidationAppError
from app.services import agent_workforce_proposal_service as proposal_service
from app.services.agent_governance import governed_agent_execution


@pytest.mark.asyncio
async def test_runtime_manager_proposal_requires_runtime_context():
    with pytest.raises(ValidationAppError, match="active Agent runtime context"):
        await proposal_service.create_manager_proposal_from_runtime(
            object(),
            tenant_id=uuid.uuid4(),
            sponsor_user_id=uuid.uuid4(),
            operation="staffing_proposal",
            title="Add developer",
            rationale="Capacity gap",
            requested_name="AI Developer",
        )


@pytest.mark.asyncio
async def test_runtime_manager_proposal_uses_bound_agent_identity(monkeypatch):
    tenant_id = uuid.uuid4()
    manager_id = uuid.uuid4()
    run_id = uuid.uuid4()
    captured = {}

    async def create(*args, **kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(proposal_service, "create_manager_proposal", create)

    async with governed_agent_execution(
        tenant_id=tenant_id,
        agent_instance_id=manager_id,
        run_id=run_id,
    ):
        await proposal_service.create_manager_proposal_from_runtime(
            object(),
            tenant_id=tenant_id,
            sponsor_user_id=uuid.uuid4(),
            operation="staffing_proposal",
            title="Add developer",
            rationale="Capacity gap",
            requested_name="AI Developer",
        )

    assert captured["manager_agent_instance_id"] == manager_id
    assert captured["tenant_id"] == tenant_id
    assert captured["configuration"]["manager_runtime_run_id"] == str(run_id)
