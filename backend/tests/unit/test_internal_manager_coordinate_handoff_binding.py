"""Focused unit coverage for the Internal Manager coordinate-handoff tool binding."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.ai.tool_registry import build_default_registry
from app.services import agent_tool_governance, license_service


@pytest.mark.asyncio
async def test_internal_manager_coordinate_handoff_forwards_governed_context(monkeypatch):
    registry = build_default_registry()
    tenant_id = uuid4()
    delegator_id = uuid4()
    delegate_id = uuid4()
    source_id = uuid4()
    child_id = uuid4()
    delegation_id = uuid4()
    run_id = uuid4()
    expires_at = "2030-01-01T00:00:00+00:00"
    captured = {}

    async def allow_entitlement(*args, **kwargs):
        return None

    async def allow_authorized(*args, **kwargs):
        return None

    async def create_child(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return SimpleNamespace(
            id=child_id,
            policy_context={"delegation_id": str(delegation_id)},
            executor_id=delegate_id,
            status=SimpleNamespace(value="assigned"),
        )

    monkeypatch.setattr(license_service, "assert_feature_entitlement", allow_entitlement)
    monkeypatch.setattr(agent_tool_governance, "assert_authorized", allow_authorized)
    monkeypatch.setattr(
        "app.services.agent_delegation_service.create_delegated_work_item",
        create_child,
    )

    context_token = agent_tool_governance._AGENT_CONTEXT.set(
        (tenant_id, delegator_id, run_id, None)
    )
    db = object()
    scopes = {"actions": ["run.execute"]}
    try:
        result = await registry.execute(
            "workforce_coordinate_handoff",
            {
                "source_work_item_id": str(source_id),
                "delegate_agent_instance_id": str(delegate_id),
                "scopes": scopes,
                "expires_at": expires_at,
                "max_chain_depth": 2,
                "title": "Bounded delegated task",
                "description": "Test handoff only",
                "context": {"purpose": "unit-test"},
                "artifacts": [{"kind": "test-evidence"}],
                "idempotency_key": "coordinate-handoff-binding-test",
            },
            permissions={"run.execute"},
            allowed_tools={"workforce_coordinate_handoff"},
            db=db,
            tenant_id=tenant_id,
            agent_instance_id=delegator_id,
        )
    finally:
        agent_tool_governance._AGENT_CONTEXT.reset(context_token)

    assert result == {
        "work_item_id": str(child_id),
        "delegation_id": str(delegation_id),
        "delegate_agent_instance_id": str(delegate_id),
        "status": "assigned",
        "scope": "tenant-scoped governed Agent-to-Agent handoff; delegation authority and chain depth are enforced",
    }
    assert captured == {
        "db": db,
        "tenant_id": tenant_id,
        "source_work_item_id": source_id,
        "delegator_agent_instance_id": delegator_id,
        "delegate_agent_instance_id": delegate_id,
        "scopes": scopes,
        "expires_at": datetime(2030, 1, 1, tzinfo=timezone.utc),
        "max_chain_depth": 2,
        "title": "Bounded delegated task",
        "description": "Test handoff only",
        "context": {"purpose": "unit-test"},
        "artifacts": [{"kind": "test-evidence"}],
        "idempotency_key": "coordinate-handoff-binding-test",
    }
