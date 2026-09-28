import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ValidationAppError
from app.models.agent_instance import AgentInstanceStatus
from app.services import agent_template_service as service


@pytest.mark.asyncio
async def test_provision_instance_rejects_direct_activation():
    db = SimpleNamespace()
    with pytest.raises(ValidationAppError, match="governed workforce activation path"):
        await service.provision_instance(
            db,
            tenant_id=uuid.uuid4(),
            template_id=uuid.uuid4(),
            name="Agent",
            sponsor_user_id=uuid.uuid4(),
            approved_by_user_id=uuid.uuid4(),
            activate=True,
        )


@pytest.mark.asyncio
async def test_transition_instance_rejects_direct_enablement():
    db = SimpleNamespace()
    with pytest.raises(ValidationAppError, match="fresh governed workforce decision"):
        await service.transition_instance(
            db,
            tenant_id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            target_status=AgentInstanceStatus.ENABLED,
            requested_by_user_id=uuid.uuid4(),
            approved_by_user_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_publish_template_rejects_cross_tenant_approver(monkeypatch):
    tenant_id, approver = uuid.uuid4(), uuid.uuid4()
    template = SimpleNamespace(
        id=uuid.uuid4(),
        status=SimpleNamespace(value="draft"),
        evaluation_policy={},
    )

    class Result:
        def scalar_one_or_none(self):
            return template

    async def reject(*args, **kwargs):
        raise ValidationAppError("approved_by_user_id does not belong to tenant")

    db = SimpleNamespace(
        execute=AsyncMock(return_value=Result()),
        flush=AsyncMock(),
        refresh=AsyncMock(),
    )
    monkeypatch.setattr(service, "assert_users_belong_to_tenant", reject)
    with pytest.raises(ValidationAppError, match="approved_by_user_id"):
        await service.publish_template(
            db,
            tenant_id=tenant_id,
            template_id=template.id,
            approved_by_user_id=approver,
        )
    db.flush.assert_not_awaited()
