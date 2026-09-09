from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import agent_tool_governance


class _Result:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return SimpleNamespace(all=lambda: list(self._items))


class _DB:
    def __init__(self, approval):
        self.approval = approval
        self.flush_count = 0

    async def execute(self, _query):
        if self.approval is not None and self.approval.status == "approved":
            return _Result([self.approval])
        return _Result([])

    async def flush(self):
        self.flush_count += 1


@pytest.mark.asyncio
async def test_approved_agent_tool_request_is_consumed_before_execution():
    tenant_id = uuid4()
    run_id = uuid4()
    approval = SimpleNamespace(
        tenant_id=tenant_id,
        run_id=run_id,
        tool_name="send_email",
        tool_call_id="call-1",
        arguments={"to": ["user@example.com"]},
        status="approved",
    )
    db = _DB(approval)

    claimed = await agent_tool_governance._resolve_approval(
        db,
        tenant_id=tenant_id,
        run_id=run_id,
        tool_name="send_email",
        arguments={"to": ["user@example.com"]},
    )

    assert claimed is approval
    assert approval.status == "consumed"
    assert db.flush_count == 1


@pytest.mark.asyncio
async def test_consumed_agent_tool_request_cannot_be_replayed():
    tenant_id = uuid4()
    run_id = uuid4()
    approval = SimpleNamespace(
        tenant_id=tenant_id,
        run_id=run_id,
        tool_name="send_email",
        tool_call_id="call-1",
        arguments={"to": ["user@example.com"]},
        status="approved",
    )
    db = _DB(approval)

    first = await agent_tool_governance._resolve_approval(
        db, tenant_id=tenant_id, run_id=run_id, tool_name="send_email", arguments=approval.arguments
    )
    second = await agent_tool_governance._resolve_approval(
        db, tenant_id=tenant_id, run_id=run_id, tool_name="send_email", arguments=approval.arguments
    )

    assert first is approval
    assert second is None
    assert approval.status == "consumed"
