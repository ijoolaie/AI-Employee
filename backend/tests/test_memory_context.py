from app.memory.context import build_memory_query, memory_settings
from app.ai.prompt_assembly import ExecutionContext, assemble_employee_prompt

def test_memory_policy_is_opt_in_and_requires_explicit_fields():
    assert memory_settings({})["enabled"] is False
    cfg = memory_settings({"memory": {"enabled": True, "top_k": 6, "query_fields": ["message"], "min_score": 0.42}})
    assert cfg == {"enabled": True, "top_k": 6, "query_fields": ["message"], "min_score": 0.42}

def test_memory_query_only_uses_declared_fields():
    query = build_memory_query({"message": "user prefers Persian", "secret": "no"}, ["message"])
    assert "user prefers Persian" in query
    assert "secret" not in query

def test_memory_query_rejects_missing_fields():
    try:
        build_memory_query({"message": "x"}, ["question"])
    except Exception as exc:
        assert "did not match" in str(exc)
    else:
        raise AssertionError("expected validation failure")

def test_memory_context_is_assembled_as_reference_material():
    assembly = assemble_employee_prompt(
        prompt_template="Use remembered user facts when relevant.",
        prompt_version="4",
        context=ExecutionContext(
            input_data={"message": "preferences"},
            memory=[{"id": "m1", "memory_type": "preference", "content": "User prefers concise answers.", "importance": 4, "score": 0.91}],
        ),
    )
    system = assembly.messages[0].content
    assert "## Memory Context" in system
    assert "User prefers concise answers." in system
