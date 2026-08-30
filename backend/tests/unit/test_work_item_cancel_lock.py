"""Regression coverage for the database row lock used by cancel."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.api.v1.work_items import _get_work_item
from app.models.work_item import WorkItem


@pytest.mark.asyncio
async def test_get_work_item_for_update_uses_tenant_scoped_row_lock_for_cancel() -> None:
    tenant_id = uuid4()
    work_item_id = uuid4()
    item = WorkItem(id=work_item_id, tenant_id=tenant_id)
    result = MagicMock()
    result.scalar_one_or_none.return_value = item
    db = AsyncMock()
    db.execute.return_value = result

    loaded = await _get_work_item(db, work_item_id, tenant_id, for_update=True)

    assert loaded is item
    stmt = db.execute.await_args.args[0]
    assert stmt._for_update_arg is not None
    assert len(stmt._where_criteria) == 2
