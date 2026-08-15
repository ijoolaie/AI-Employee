from app.ai.prompt_assembly import ExecutionContext, assemble_employee_prompt
from app.core.exceptions import ValidationAppError


def test_prompt_assembly_renders_template_and_json_input():
    assembly = assemble_employee_prompt(
        prompt_template="Answer briefly about {message}.",
        prompt_version="2",
        context=ExecutionContext(
            input_data={"message": "LM Studio"},
            rules={"max_length": "short"},
        ),
    )

    assert assembly.assembly_version == "3"
    assert assembly.prompt_version == "2"
    assert assembly.messages[0].role == "system"
    assert "Answer briefly about LM Studio." in assembly.messages[0].content
    assert "Execution Rules" in assembly.messages[0].content
    assert '"message": "LM Studio"' in assembly.messages[1].content
    assert assembly.tools == []
    assert assembly.metadata["message_count"] == 2
    assert assembly.metadata["context_sections"] == ["rules"]


def test_prompt_assembly_defaults_system_prompt_for_empty_template():
    assembly = assemble_employee_prompt(
        prompt_template="",
        prompt_version="1",
        context=ExecutionContext(input_data={"message": "hello"}),
    )
    assert assembly.messages[0].content == "You are an AI Employee."


def test_prompt_assembly_rejects_missing_template_field():
    try:
        assemble_employee_prompt(
            prompt_template="Hello {name}",
            prompt_version="1",
            context=ExecutionContext(input_data={"message": "hello"}),
        )
    except ValidationAppError as exc:
        assert "missing input fields" in str(exc).lower()
        assert exc.details["missing"] == ["name"]
    else:
        raise AssertionError("Expected ValidationAppError")

def test_prompt_assembly_renders_reserved_input_json_field():
    assembly = assemble_employee_prompt(
        prompt_template="Input JSON: {input_json}",
        prompt_version="1",
        context=ExecutionContext(
            input_data={"file_id": "abc", "message": "hello"},
        ),
    )

    assert '"file_id": "abc"' in assembly.messages[0].content
    assert '"message": "hello"' in assembly.messages[0].content
    assert assembly.messages[0].content.count('"file_id"') == 1
