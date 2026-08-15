"""JSON Schema validation tests for Employee Run input/output contracts."""

import pytest

from app.core.exceptions import ValidationAppError
from app.services.schema_validation import validate_json_data, validate_schema_definition


def test_valid_input_schema_accepts_matching_payload():
    schema = {
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
        "additionalProperties": False,
    }
    validate_json_data({"message": "hello"}, schema, field_name="input_data")


def test_input_schema_rejects_wrong_type():
    schema = {
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    }
    with pytest.raises(ValidationAppError) as exc_info:
        validate_json_data({"message": 123}, schema, field_name="input_data")

    assert exc_info.value.status_code == 422
    assert exc_info.value.details["path"] == "message"
    assert exc_info.value.details["validator"] == "type"
    assert exc_info.value.details["validation_version"] == "2020-12-v1"


def test_input_schema_rejects_missing_required_field():
    schema = {
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    }
    with pytest.raises(ValidationAppError) as exc_info:
        validate_json_data({}, schema, field_name="input_data")

    assert exc_info.value.details["path"] == "$"
    assert exc_info.value.details["validator"] == "required"


def test_output_schema_validates_the_actual_run_output_shape():
    schema = {
        "type": "object",
        "properties": {"text": {"type": "string", "minLength": 1}},
        "required": ["text"],
        "additionalProperties": False,
    }
    validate_json_data({"text": "Understood."}, schema, field_name="output_data")

    with pytest.raises(ValidationAppError):
        validate_json_data({"text": ""}, schema, field_name="output_data")


def test_empty_schema_remains_unconstrained():
    validate_json_data({"anything": [1, 2, 3]}, {}, field_name="input_data")


def test_invalid_schema_definition_is_rejected():
    invalid_schema = {"type": "not-a-json-schema-type"}
    with pytest.raises(ValidationAppError) as exc_info:
        validate_schema_definition(invalid_schema, field_name="input_schema")

    assert exc_info.value.details["field"] == "input_schema"


def test_nested_constraints_and_enum_are_enforced():
    schema = {
        "type": "object",
        "properties": {
            "profile": {
                "type": "object",
                "properties": {
                    "age": {"type": "integer", "minimum": 18},
                    "role": {"enum": ["admin", "operator"]},
                },
                "required": ["age", "role"],
            }
        },
        "required": ["profile"],
    }
    validate_json_data(
        {"profile": {"age": 30, "role": "operator"}},
        schema,
        field_name="input_data",
    )

    with pytest.raises(ValidationAppError):
        validate_json_data(
            {"profile": {"age": 17, "role": "viewer"}},
            schema,
            field_name="input_data",
        )


def test_local_json_pointer_reference_is_supported():
    schema = {
        "type": "object",
        "$defs": {"message": {"type": "string", "minLength": 1}},
        "properties": {"message": {"$ref": "#/$defs/message"}},
        "required": ["message"],
    }
    validate_json_data({"message": "hello"}, schema, field_name="input_data")


def test_external_json_reference_is_rejected():
    schema = {"$ref": "https://example.com/schema.json"}
    with pytest.raises(ValidationAppError) as exc_info:
        validate_schema_definition(schema, field_name="input_schema")

    assert exc_info.value.details["path"] == "$.$ref"


def test_format_checker_rejects_invalid_email():
    schema = {
        "type": "object",
        "properties": {"email": {"type": "string", "format": "email"}},
        "required": ["email"],
    }
    with pytest.raises(ValidationAppError) as exc_info:
        validate_json_data({"email": "not-an-email"}, schema, field_name="input_data")

    assert exc_info.value.details["validator"] == "format"
