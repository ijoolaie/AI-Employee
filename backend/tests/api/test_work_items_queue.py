from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_work_item_queue_is_tenant_scoped(client: AsyncClient, auth_headers, db_session):
    """The queue must never return another tenant's WorkItems."""
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

    response = await client.get("/api/v1/work-items", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    ids = {item["id"] for item in payload}
    assert str(own.id) in ids
    assert str(other.id) not in ids
