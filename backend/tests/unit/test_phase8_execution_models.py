from uuid import uuid4

from app.models.agent_definition import AgentDefinition
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus


def test_work_item_defaults_and_executor_types() -> None:
    item = WorkItem(
        tenant_id=uuid4(),
        title="Process customer request",
        idempotency_key="test-1",
    )
    assert item.status is WorkItemStatus.DRAFT
    assert item.executor_type is None
    assert ExecutorType.HUMAN.value == "human"
    assert ExecutorType.AGENT.value == "agent"


def test_agent_definition_contains_policy_boundaries() -> None:
    agent = AgentDefinition(
        tenant_id=uuid4(),
        slug="support-triage",
        name="Support Triage",
    )
    assert agent.version == 1
    assert agent.capabilities == []
    assert agent.allowed_tools == []
    assert agent.policy_requirements == {}


def test_agent_instance_is_tenant_scoped_and_lifecycle_aware() -> None:
    instance = AgentInstance(
        tenant_id=uuid4(),
        agent_definition_id=uuid4(),
        name="Support Triage Production",
    )
    assert instance.status is AgentInstanceStatus.ENABLED
    assert instance.max_concurrency == 1
