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
    assert WorkItem.status.property.columns[0].default.arg is WorkItemStatus.DRAFT
    assert item.executor_type is None
    assert ExecutorType.HUMAN.value == "human"
    assert ExecutorType.AGENT.value == "agent"


def test_agent_definition_contains_policy_boundaries() -> None:
    agent = AgentDefinition(
        tenant_id=uuid4(),
        slug="support-triage",
        name="Support Triage",
    )
    assert AgentDefinition.version.property.columns[0].default.arg == 1
    assert AgentDefinition.capabilities.property.columns[0].default.is_callable
    assert AgentDefinition.allowed_tools.property.columns[0].default.is_callable
    assert AgentDefinition.policy_requirements.property.columns[0].default.is_callable


def test_agent_instance_is_tenant_scoped_and_lifecycle_aware() -> None:
    instance = AgentInstance(
        tenant_id=uuid4(),
        agent_definition_id=uuid4(),
        name="Support Triage Production",
    )
    assert AgentInstance.status.property.columns[0].default.arg is AgentInstanceStatus.ENABLED
    assert AgentInstance.max_concurrency.property.columns[0].default.arg == 1
