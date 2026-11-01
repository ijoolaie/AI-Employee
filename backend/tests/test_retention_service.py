from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.services.retention_service import enforce_retention


class Result:
    def __init__(self, rowcount=0, rows=None):
        self.rowcount = rowcount
        self._rows = rows or []

    def scalars(self):
        return self

    def all(self):
        return self._rows


@pytest.mark.asyncio
async def test_retention_rejects_unsafe_window():
    with pytest.raises(ValueError):
        await enforce_retention(None, tenant_id=uuid4(), retention_days=0)


@pytest.mark.asyncio
async def test_retention_is_tenant_scoped_and_idempotent_shape(monkeypatch):
    class DB:
        def __init__(self):
            self.calls = []

        async def execute(self, statement):
            self.calls.append(statement)
            return Result()

        async def flush(self):
            return None

    db = DB()
    tenant = uuid4()
    now = datetime(2026, 9, 5, tzinfo=timezone.utc)
    result = await enforce_retention(db, tenant_id=tenant, retention_days=365, now=now)
    assert result["tenant_id"] == str(tenant)
    assert result["usage_events_deleted"] == 0
    assert result["memory_rows_deleted"] == 0
    assert result["files_soft_deleted"] == 0
    assert result["customer_slots_deleted"] == 0
    assert len(db.calls) == 4
    purge_sql = str(db.calls[3].compile(dialect=postgresql.dialect()))
    assert "customer_conversation_slots.tenant_id" in purge_sql
    assert "customer_conversation_slots.expires_at" in purge_sql
    assert "FOR UPDATE SKIP LOCKED" in purge_sql
    assert "LIMIT" in purge_sql
