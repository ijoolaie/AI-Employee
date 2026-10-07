from pathlib import Path


BILLING = Path("app/services/billing_service.py").read_text()
WORKFLOW = Path("app/services/workflow_service.py").read_text()


def _function_block(source: str, name: str, next_name: str) -> str:
    start = source.index("async def " + name)
    end = source.index("async def " + next_name, start)
    return source[start:end]


def test_quota_checks_lock_the_tenant_row_before_counting_usage():
    for name, next_name in (
        ("enforce_run_quota", "enforce_employee_quota"),
        ("enforce_employee_quota", "enforce_workflow_quota"),
        ("enforce_workflow_quota", "platform_mrr"),
    ):
        block = _function_block(BILLING, name, next_name)
        assert "_lock_tenant_for_quota(db, tenant_id=tenant_id)" in block

    helper_start = BILLING.index("async def _lock_tenant_for_quota")
    helper_end = BILLING.index("async def enforce_run_quota", helper_start)
    helper = BILLING[helper_start:helper_end]
    assert "select(Tenant)" in helper
    assert ".with_for_update()" in helper


def test_workflow_creation_is_inside_the_same_tenant_quota_fence():
    start = WORKFLOW.index("async def create_workflow(")
    end = WORKFLOW.index("async def create_workflow_version", start)
    block = WORKFLOW[start:end]
    assert "await billing_service.enforce_workflow_quota(db, tenant_id=tenant_id)" in block
    assert block.index("enforce_workflow_quota") < block.index("db.add(workflow)")
