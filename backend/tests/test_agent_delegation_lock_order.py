from pathlib import Path


def test_validate_delegation_locks_workitems_before_delegations():
    path = Path(__file__).parents[1] / "app" / "services" / "agent_delegation_service.py"
    source = path.read_text(encoding="utf-8")
    fn = source[source.index("async def validate_delegation("):]

    workitem_lock = fn.index("select(WorkItem).where(")
    delegation_lock = fn.index(
        "select(AgentDelegation).where(",
        fn.index("locked_delegations"),
    )
    assert workitem_lock < delegation_lock
    assert "execution_options(populate_existing=True).with_for_update()" in fn
    assert "work_item_ids = list(dict.fromkeys(reversed(source_ids)))" in fn
