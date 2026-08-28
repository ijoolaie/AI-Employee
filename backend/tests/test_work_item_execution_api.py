from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.work_items import history
from app.models.audit_log import AuditLog


class ScalarResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return self

    def all(self):
        return self._values


class HistoryDB:
    def __init__(self, item, entries):
        self.item = item
        self.entries = entries

    async def get(self, model, key):
        return self.item if key == self.item.id else None

    async def execute(self, stmt):
        # The route's SQL statement is tenant-scoped; this fake DB mirrors the
        # resulting database behavior by returning only already-authorized rows.
        return ScalarResult(self.entries)


@pytest.mark.asyncio
async def test_history_returns_only_current_tenant_events():
    tenant_id = uuid4()
    work_item_id = uuid4()
    user = SimpleNamespace(tenant_id=tenant_id, id=uuid4())
    item = SimpleNamespace(id=work_item_id, tenant_id=tenant_id)
    entry = AuditLog(
        id=uuid4(), tenant_id=tenant_id, actor_type="user", actor_id=user.id,
        action="work_item.assigned", resource_type="work_item",
        resource_id=str(work_item_id), status="success", metadata_={"x": 1},
        created_at=datetime.now(timezone.utc),
    )
    result = await history(work_item_id, limit=100, db=HistoryDB(item, [entry]), current_user=user)
    assert len(result) == 1
    assert result[0].id == entry.id
    assert result[0].metadata == {"x": 1}


@pytest.mark.asyncio
async def test_history_hides_work_item_from_other_tenant():
    owner_tenant = uuid4()
    foreign_tenant = uuid4()
    item = SimpleNamespace(id=uuid4(), tenant_id=owner_tenant)
    user = SimpleNamespace(tenant_id=foreign_tenant, id=uuid4())

    with pytest.raises(HTTPException) as exc:
        await history(item.id, limit=100, db=HistoryDB(item, []), current_user=user)

    assert exc.value.status_code == 404
    assert exc.value.detail == "work item not found"


@pytest.mark.asyncio
async def test_history_query_is_tenant_scoped_for_matching_work_item():
    tenant_id = uuid4()
    work_item_id = uuid4()
    user = SimpleNamespace(tenant_id=tenant_id, id=uuid4())
    item = SimpleNamespace(id=work_item_id, tenant_id=tenant_id)
    other_tenant_entry = AuditLog(
        id=uuid4(), tenant_id=uuid4(), actor_type="user", actor_id=uuid4(),
        action="work_item.assigned", resource_type="work_item",
        resource_id=str(work_item_id), status="success", metadata_={},
        created_at=datetime.now(timezone.utc),
    )
    result = await history(work_item_id, limit=100, db=HistoryDB(item, []), current_user=user)
    assert result == []
    assert other_tenant_entry.tenant_id != tenant_id
