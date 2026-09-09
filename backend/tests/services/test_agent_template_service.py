import uuid
from types import SimpleNamespace

import pytest

from app.core.exceptions import ValidationAppError
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
