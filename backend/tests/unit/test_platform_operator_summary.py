from types import SimpleNamespace
from uuid import uuid4

from app.services.platform_operator_summary import operator_summary


def item(tenant, status, executor="agent"):
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant,
        correlation_id="corr-summary",
        status=SimpleNamespace(value=status),
        executor_type=SimpleNamespace(value=executor),
        output_data={},
    )


def test_operator_summary_combines_command_center_models():
    tenant = uuid4()
    result = operator_summary(
        [item(tenant, "failed"), item(tenant, "waiting_approval", "human")],
        tenant_id=tenant,
        actor_tenant_id=tenant,
    )

    assert result["overview"]["total_work_items"] == 2
    assert result["attention_count"] == 2
    assert result["actionable_count"] == 2
    assert result["attention"][0]["status"] == "failed"
