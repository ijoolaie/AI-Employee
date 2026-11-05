from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.api.v1.runs import _employee_labels


@pytest.mark.asyncio
async def test_run_employee_label_lookup_is_tenant_scoped():
    tenant_id = uuid4()
    employee_id = uuid4()

    class DB:
        statement = None

        async def execute(self, statement):
            self.statement = statement
            return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))

    db = DB()
    labels = await _employee_labels(db, tenant_id=tenant_id, employee_ids=[employee_id])

    compiled = db.statement.compile(dialect=postgresql.dialect())
    assert labels == {}
    assert "employees.tenant_id" in str(compiled)
    assert tenant_id in compiled.params.values()
    assert any(
        employee_id == value or (isinstance(value, (list, tuple)) and employee_id in value)
        for value in compiled.params.values()
    )
