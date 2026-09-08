from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.services import agent_governance
from app.memory import service as memory_service


@pytest.mark.asyncio
async def test_agent_memory_context_is_run_employee_and_version_scoped():
    tenant_id = uuid4()
    agent_id = uuid4()
    run_id = uuid4()
    employee_id = uuid4()
    version_id = uuid4()

    async with agent_governance.governed_agent_execution(
        tenant_id=tenant_id,
        agent_instance_id=agent_id,
        run_id=run_id,
        employee_id=employee_id,
        employee_version_id=version_id,
    ):
        memory_service._assert_agent_memory_scope(
            tenant_id=tenant_id,
            employee_id=employee_id,
            employee_version_id=version_id,
            run_id=run_id,
        )

        with pytest.raises(ValidationAppError, match="Employee boundary"):
            memory_service._assert_agent_memory_scope(
                tenant_id=tenant_id,
                employee_id=uuid4(),
                employee_version_id=version_id,
                run_id=run_id,
            )

        with pytest.raises(ValidationAppError, match="EmployeeVersion boundary"):
            memory_service._assert_agent_memory_scope(
                tenant_id=tenant_id,
                employee_id=employee_id,
                employee_version_id=uuid4(),
                run_id=run_id,
            )

        with pytest.raises(ValidationAppError, match="Run boundary"):
            memory_service._assert_agent_memory_scope(
                tenant_id=tenant_id,
                employee_id=employee_id,
                employee_version_id=version_id,
                run_id=uuid4(),
            )


@pytest.mark.asyncio
async def test_agent_memory_context_rejects_cross_tenant_access():
    tenant_id = uuid4()
    async with agent_governance.governed_agent_execution(
        tenant_id=tenant_id,
        agent_instance_id=uuid4(),
        run_id=uuid4(),
        employee_id=uuid4(),
        employee_version_id=uuid4(),
    ):
        with pytest.raises(ValidationAppError, match="tenant boundary"):
            memory_service._assert_agent_memory_scope(
                tenant_id=uuid4(),
                employee_id=uuid4(),
            )
