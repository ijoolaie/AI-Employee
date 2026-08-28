
@pytest.mark.asyncio
async def test_assign_human_and_dispatch():
    tenant_id = uuid4()
    item = work_item(tenant_id)
    service = UnifiedExecutionService(SimpleNamespace(get=None), human_executor=HumanRuntime())

    service.assign_human(item, uuid4())
    result = await service.dispatch(item)

    assert result.dispatched is True
    assert item.executor_type is ExecutorType.HUMAN
    assert item.status is WorkItemStatus.RUNNING


@pytest.mark.asyncio
async def test_cross_tenant_agent_is_rejected():
    service = UnifiedExecutionService(SimpleNamespace(get=None))
    item = work_item(uuid4())

    with pytest.raises(ExecutionError, match="cross-tenant"):
        await service.assign_agent(item, agent(uuid4()))


@pytest.mark.asyncio
async def test_approval_gate_prevents_dispatch():