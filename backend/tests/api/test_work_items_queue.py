from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1.work_items import list_work_items
from app.models.work_item import WorkItem, WorkItemStatus


@pytest.mark.asyncio
async def test_work_item_queue_is_tenant_scoped():
    """The queue query must include the current tenant in its SQL predicate."""
    tenant_id = uuid4()
    other_tenant_id = uuid4()
    own = WorkItem(
        tenant_id=tenant_id,
        title="own item",
        status=WorkItemStatus.READY,
        input_data={},
        policy_context={},
        idempotency_key=f"queue-own-{uuid4()}",
    )
    other = WorkItem(
        tenant_id=other_tenant_id,
        title="other item",
        status=WorkItemStatus.READY,
        input_data={},
        policy_context={},
        idempotency_key=f"queue-other-{uuid4()}",
    )

    captured = {}

    class Result:
        def scalars(self):
            return self

        def all(self):
            return [own]

    class Db:
        async def execute(self, stmt):
            captured["statement"] = stmt
            return Result()

    payload = await list_work_items(
        db=Db(),
        current_user=SimpleNamespace(tenant_id=tenant_id),
        limit=100,
    )

    assert [item.id for item in payload] == [own.id]
    statement = captured["statement"]
    assert "work_items.tenant_id" in str(statement)
    assert any(value == tenant_id for value in statement.compile().params.values())
    assert other.id not in {item.id for item in payload}
