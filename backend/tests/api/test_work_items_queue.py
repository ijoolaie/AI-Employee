from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1.work_items import list_work_items


@pytest.mark.asyncio
async def test_work_item_queue_is_tenant_scoped(db_session):
    """The queue query must never return another tenant's WorkItems."""
    from app.models.work_item import WorkItem, WorkItemStatus

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
    db_session.add_all([own, other])
    await db_session.commit()

    current_user = SimpleNamespace(tenant_id=tenant_id)
    payload = await list_work_items(db=db_session, current_user=current_user)
    ids = {item.id for item in payload}

    assert own.id in ids
    assert other.id not in ids
