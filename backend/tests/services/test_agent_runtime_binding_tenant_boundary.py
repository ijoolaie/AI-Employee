from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.core.exceptions import ConflictError
from app.models.agent_instance import AgentInstanceStatus
from app.services import agent_runtime_binding


class _Result:
    def __init__(self, *, row=None, scalar=None):
        self._row = row
        self._scalar = scalar

    def one_or_none(self):
        return self._row

    def scalar_one_or_none(self):
        return self._scalar


class _Session:
    def __init__(self):
        self.statements = []
        self.results = [
            _Result(row=(SimpleNamespace(id=uuid4(), enabled=True, status=AgentInstanceStatus.ENABLED), SimpleNamespace(id=uuid4(), enabled=True))),
            _Result(scalar=SimpleNamespace(active=True, revoked_at=None, expires_at=None)),
            _Result(row=None),
        ]

    async def execute(self, statement):
        self.statements.append(statement)
        return self.results.pop(0)


@pytest.mark.asyncio
async def test_runtime_binding_resolution_rejects_employee_version_from_other_tenant():
    tenant_id = uuid4()
    session = _Session()

    with pytest.raises(ConflictError, match="runtime binding is not configured"):
        await agent_runtime_binding.resolve_employee_version(
            session,
            tenant_id=tenant_id,
            agent_instance_id=uuid4(),
        )

    binding_query = session.statements[2]
    sql = str(binding_query.compile(dialect=postgresql.dialect()))
    assert "JOIN employees ON employees.id = employee_versions.employee_id" in sql
    assert "employees.tenant_id =" in sql
