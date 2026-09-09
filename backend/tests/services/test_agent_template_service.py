import uuid
from types import SimpleNamespace

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
