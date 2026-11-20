"""Regression coverage for tenant-scoped outbox deduplication."""

import uuid

import pytest

from sqlalchemy.dialects import postgresql

from app.services import outbox_service


def test_dedupe_lookup_binds_tenant_identity():
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    stmt_a = outbox_service._dedupe_lookup("same-key", tenant_a)
    stmt_b = outbox_service._dedupe_lookup("same-key", tenant_b)

    sql_a = str(stmt_a.compile(dialect=postgresql.dialect()))
    sql_b = str(stmt_b.compile(dialect=postgresql.dialect()))

    assert "tenant_id" in sql_a
    assert "tenant_id" in sql_b
    assert tenant_a in stmt_a.compile(dialect=postgresql.dialect()).params.values()
    assert tenant_b in stmt_b.compile(dialect=postgresql.dialect()).params.values()


def test_tenantless_dedupe_remains_global():
    stmt = outbox_service._dedupe_lookup("global-key", None)
    sql = str(stmt.compile(dialect=postgresql.dialect()))

    assert "tenant_id IS NULL" in sql
    assert "dedupe_key" in sql


@pytest.mark.asyncio
async def test_outbox_enqueue_strips_forged_agent_governance_without_active_context(monkeypatch):
    from app.services import agent_tool_governance

    class _DB:
        def __init__(self):
            self.added = None

        def add(self, message):
            self.added = message

        async def flush(self):
            return None

    monkeypatch.setattr(agent_tool_governance, "_AGENT_CONTEXT", agent_tool_governance.ContextVar(
        "isolated_agent_context_test", default=None
    ))
    monkeypatch.setattr(agent_tool_governance, "_CURRENT_TOOL", agent_tool_governance.ContextVar(
        "isolated_current_tool_test", default=None
    ))
    db = _DB()
    tenant_id = uuid.uuid4()
    forged = {
        "tenant_id": str(tenant_id),
        "agent_instance_id": str(uuid.uuid4()),
        "run_id": str(uuid.uuid4()),
        "tool_name": "email.send",
    }

    message = await outbox_service.enqueue(
        db,
        kind="email.send",
        tenant_id=tenant_id,
        payload={"to": ["victim@example.test"], "_agent_governance": forged},
    )

    assert message is db.added
    assert "_agent_governance" not in message.payload


@pytest.mark.asyncio
async def test_outbox_enqueue_rejects_active_agent_context_for_other_tenant(monkeypatch):
    from app.services import agent_tool_governance

    class _DB:
        def add(self, _message):
            raise AssertionError("mismatched tenant must be rejected before persistence")

        async def flush(self):
            raise AssertionError("mismatched tenant must be rejected before flush")

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    monkeypatch.setattr(agent_tool_governance, "_AGENT_CONTEXT", agent_tool_governance.ContextVar(
        "isolated_agent_context_mismatch_test", default=(tenant_a, uuid.uuid4(), uuid.uuid4(), None)
    ))
    monkeypatch.setattr(agent_tool_governance, "_CURRENT_TOOL", agent_tool_governance.ContextVar(
        "isolated_current_tool_mismatch_test", default="email.send"
    ))

    import pytest
    with pytest.raises(ValueError, match="Agent outbox tenant context mismatch"):
        await outbox_service.enqueue(
            _DB(),
            kind="email.send",
            tenant_id=tenant_b,
            payload={"to": ["victim@example.test"]},
        )
