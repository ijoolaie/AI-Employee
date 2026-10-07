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

    async def execute(self, query):
        if self.approval is None or self.approval.status != "approved":
            return _Result([])

        # Model the SQL predicate for tool_call_id so this double cannot
        # accidentally return an approval that the real query would exclude.
        params = query.compile().params
        call_id = next(
            (value for key, value in params.items() if "tool_call_id" in key),
            None,
        )
        if call_id != self.approval.tool_call_id:
            return _Result([])
        return _Result([self.approval])

    async def flush(self):
        self.flush_count += 1


@pytest.mark.asyncio
async def test_approved_request_remains_approved_for_exact_tool_call_resolution():
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

    resolved = await agent_tool_governance._resolve_approval(
        db,
        tenant_id=tenant_id,
        run_id=run_id,
        tool_name="send_email",
        tool_call_id="call-1",
        arguments=approval.arguments,
    )

    assert resolved is approval
    assert approval.status == "approved"
    assert db.flush_count == 0

    await agent_tool_governance._consume_approval(db, approval)
    assert approval.status == "consumed"
    assert db.flush_count == 1


@pytest.mark.asyncio
async def test_approval_cannot_be_reused_for_a_different_tool_call_id():
    tenant_id = uuid4()
    run_id = uuid4()
    approval = SimpleNamespace(
        tenant_id=tenant_id,
        run_id=run_id,
        tool_name="send_email",
        tool_call_id="approved-call",
        arguments={"to": ["user@example.com"]},
        status="approved",
    )
    db = _DB(approval)

    resolved = await agent_tool_governance._resolve_approval(
        db,
        tenant_id=tenant_id,
        run_id=run_id,
        tool_name="send_email",
        tool_call_id="different-call",
        arguments=approval.arguments,
    )

    assert resolved is None
    assert approval.status == "approved"
    assert db.flush_count == 0


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
        db,
        tenant_id=tenant_id,
        run_id=run_id,
        tool_name="send_email",
        tool_call_id="call-1",
        arguments=approval.arguments,
    )
    await agent_tool_governance._consume_approval(db, first)
    second = await agent_tool_governance._resolve_approval(
        db,
        tenant_id=tenant_id,
        run_id=run_id,
        tool_name="send_email",
        tool_call_id="call-1",
        arguments=approval.arguments,
    )

    assert first is approval
    assert second is None
    assert approval.status == "consumed"
