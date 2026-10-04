from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.services import skill_execution_service


@pytest.mark.asyncio
async def test_skill_execution_requires_active_installation(monkeypatch):
    class DB:
        async def execute(self, stmt): return SimpleNamespace(scalar_one_or_none=lambda: None)
    with pytest.raises(NotFoundError):
        await skill_execution_service.execute_installed_skill(
            DB(),
            tenant_id=uuid4(),
            employee_id=uuid4(),
            skill_package_id=uuid4(),
            input_data={},
            actor_id=None,
            request_id="req-1",
        )


def test_skill_execution_does_not_accept_provider_from_input():
    import inspect
    source = inspect.getsource(skill_execution_service.execute_installed_skill)
    assert "provider_name" not in source
    assert "get_configured_skill_provider" in source


def test_skill_execution_requires_purchase_for_commercial_skill():
    import inspect
    source = inspect.getsource(skill_execution_service.execute_installed_skill)
    assert "assert_owned" in source
