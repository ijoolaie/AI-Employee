from uuid import uuid4

import pytest

from app.agents.memory import MAX_RUNTIME_MEMORIES, build_runtime_memory


@pytest.mark.asyncio
async def test_runtime_memory_is_bounded_and_provenance_carrying(monkeypatch):
    tenant_id = uuid4()
    employee_id = uuid4()
    version_id = uuid4()

    async def fake_search(*args, **kwargs):
        return [
            {
                "id": str(uuid4()),
                "employee_id": str(employee_id),
                "memory_type": "fact",
                "content": f"memory-{index}",
                "importance": 3,
                "version": 1,
                "score": 0.9,
            }
            for index in range(MAX_RUNTIME_MEMORIES + 5)
        ]

    from app.agents import memory as memory_module
    monkeypatch.setattr(memory_module.memory_service, "search_memory", fake_search)
    monkeypatch.setattr(memory_module, "build_memory_query", lambda *_: "query")
    monkeypatch.setattr(
        memory_module,
        "memory_settings",
        lambda _: {"enabled": True, "top_k": 20, "query_fields": ["goal"], "min_score": 0.35},
    )

    result = await build_runtime_memory(
        object(),
        tenant_id=tenant_id,
        employee_id=employee_id,
        employee_version_id=version_id,
        input_data={"goal": "test"},
        rules={"memory": {"enabled": True}},
    )

    assert len(result) == MAX_RUNTIME_MEMORIES
    assert all(item["employee_id"] == str(employee_id) for item in result)
    assert all(item["employee_version_id"] == str(version_id) for item in result)
    assert all("embedding" not in item for item in result)
    assert all("metadata" not in item for item in result)


@pytest.mark.asyncio
async def test_runtime_memory_rejects_cross_tenant_result(monkeypatch):
    tenant_id = uuid4()
    employee_id = uuid4()

    async def fake_search(*args, **kwargs):
        return [{
            "id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "employee_id": str(employee_id),
            "content": "must reject",
            "importance": 3,
            "version": 1,
            "score": 0.9,
        }]

    from app.agents import memory as memory_module
    monkeypatch.setattr(memory_module.memory_service, "search_memory", fake_search)
    monkeypatch.setattr(memory_module, "build_memory_query", lambda *_: "query")
    monkeypatch.setattr(
        memory_module,
        "memory_settings",
        lambda _: {"enabled": True, "top_k": 5, "query_fields": ["goal"], "min_score": 0.35},
    )

    with pytest.raises(Exception, match="cross-tenant"):
        await build_runtime_memory(
            object(),
            tenant_id=tenant_id,
            employee_id=employee_id,
            employee_version_id=uuid4(),
            input_data={"goal": "test"},
            rules={"memory": {"enabled": True}},
        )
