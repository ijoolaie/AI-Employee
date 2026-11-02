import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy.dialects import postgresql

import app.workers.retention_worker as worker


class _Result:
    def __init__(self, *, tenant_ids=None, count=0):
        self._tenant_ids = tenant_ids
        self._count = count

    def scalars(self):
        return self

    def all(self):
        return self._tenant_ids

    def scalar_one(self):
        return self._count


class _ReadOnlySession:
    def __init__(self, tenant_ids):
        self.tenant_ids = tenant_ids
        self.count_statements = []

    async def execute(self, statement):
        sql = str(statement)
        if "FROM tenants" in sql and "SELECT tenants.id" in sql:
            return _Result(tenant_ids=self.tenant_ids)
        self.count_statements.append(statement)
        return _Result(count=1)


def test_retention_preview_reports_per_tenant_counts_without_mutations(monkeypatch):
    tenant_ids = [uuid4(), uuid4()]
    db = _ReadOnlySession(tenant_ids)

    @asynccontextmanager
    async def fake_worker_db_session():
        yield db

    monkeypatch.setattr(worker, "worker_db_session", fake_worker_db_session)
    monkeypatch.setattr(worker, "get_settings", lambda: SimpleNamespace(data_retention_days=365))

    result = asyncio.run(worker._retention_dry_run_async())

    assert result["mode"] == "dry_run"
    assert result["mutations_performed"] is False
    assert result["tenants_scanned"] == 2
    assert [row["tenant_id"] for row in result["tenant_counts"]] == [str(x) for x in tenant_ids]
    assert result["totals"] == {
        "usage_events_eligible": 2,
        "memory_rows_eligible": 2,
        "files_eligible_for_soft_delete": 2,
        "customer_slots_eligible_for_purge": 2,
    }
    assert len(db.count_statements) == 8

    # Every candidate-count query is scoped to exactly the tenant being scanned.
    for index, statement in enumerate(db.count_statements):
        compiled = statement.compile(dialect=postgresql.dialect())
        params = list(compiled.params.values())
        assert "tenant_id" in str(statement)
        assert any(value in tenant_ids for value in params)


def test_retention_preview_rejects_out_of_range_policy(monkeypatch):
    monkeypatch.setattr(worker, "get_settings", lambda: SimpleNamespace(data_retention_days=0))
    try:
        asyncio.run(worker._retention_dry_run_async())
    except ValueError as exc:
        assert "between 1 and 3650" in str(exc)
    else:
        raise AssertionError("unsafe retention window was accepted")
