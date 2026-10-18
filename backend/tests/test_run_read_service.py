from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.services import run_read_service


class _Scalars:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _Result:
    def __init__(self, values=None, one=None):
        self._values = values or []
        self._one = one

    def scalars(self):
        return _Scalars(self._values)

    def scalar_one_or_none(self):
        return self._one


class _DB:
    def __init__(self, result):
        self.result = result
        self.query = None

    async def execute(self, query):
        self.query = query
        return self.result


@pytest.mark.asyncio
async def test_list_runs_always_scopes_to_tenant_and_optional_employee():
    tenant_id = uuid4()
    employee_id = uuid4()
    run = SimpleNamespace(id=uuid4())
    db = _DB(_Result(values=[run]))

    result = await run_read_service.list_runs(
        db, tenant_id=tenant_id, employee_id=employee_id
    )

    assert result == [run]
    sql = str(db.query)
    params = db.query.compile().params
    assert "runs.tenant_id" in sql
    assert "runs.employee_id" in sql
    assert "runs.created_at DESC" in sql
    assert tenant_id in params.values()
    assert employee_id in params.values()


@pytest.mark.asyncio
async def test_get_run_scopes_lookup_to_run_and_tenant():
    tenant_id = uuid4()
    run_id = uuid4()
    run = SimpleNamespace(id=run_id)
    db = _DB(_Result(one=run))

    result = await run_read_service.get_run(
        db, run_id=run_id, tenant_id=tenant_id
    )

    assert result is run
    sql = str(db.query)
    params = db.query.compile().params
    assert "runs.id" in sql
    assert "runs.tenant_id" in sql
    assert run_id in params.values()
    assert tenant_id in params.values()


@pytest.mark.asyncio
async def test_get_run_hides_missing_or_cross_tenant_run_as_not_found():
    db = _DB(_Result(one=None))

    with pytest.raises(NotFoundError, match="Run not found"):
        await run_read_service.get_run(
            db, run_id=uuid4(), tenant_id=uuid4()
        )
