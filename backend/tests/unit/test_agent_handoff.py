from uuid import uuid4

import pytest

from app.services.agent_handoff import AgentHandoffService
from app.services.unified_execution import ExecutionError


def test_agent_handoff_preserves_tenant_context_and_payload():
    tenant = uuid4()
    payload = AgentHandoffService.handoff(
        current_agent_id=uuid4(), target_agent_id=uuid4(),
        current_tenant_id=tenant, target_tenant_id=tenant,
        context={"goal": "continue"}, artifacts=[{"id": "a1"}],
    )
    assert payload["tenant_id"] == str(tenant)
    assert payload["context"] == {"goal": "continue"}
    assert payload["artifacts"] == [{"id": "a1"}]
    assert payload["status"] == "ready"


def test_agent_handoff_rejects_cross_tenant_target():
    with pytest.raises(ExecutionError, match="cross-tenant"):
        AgentHandoffService.handoff(
            current_agent_id=uuid4(), target_agent_id=uuid4(),
            current_tenant_id=uuid4(), target_tenant_id=uuid4(),
        )


def test_agent_handoff_can_pause_for_approval():
    tenant = uuid4()
    payload = AgentHandoffService.handoff(
        current_agent_id=uuid4(), target_agent_id=uuid4(),
        current_tenant_id=tenant, target_tenant_id=tenant,
        requires_approval=True,
    )
    assert payload["status"] == "waiting_approval"
