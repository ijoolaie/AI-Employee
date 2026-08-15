"""JSON Schema validation shared by Employee definitions and Run execution.

The platform uses JSON Schema Draft 2020-12 as the contract boundary between
Employee definitions, Run inputs and model outputs. Schemas are treated as
application data, not executable code: local JSON Pointer references are
supported, while remote/external references are rejected to prevent an
Employee schema from causing the backend to resolve arbitrary network or
filesystem resources.
"""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from app.core.exceptions import ValidationAppError

VALIDATION_VERSION = "2020-12-v1"
_MAX_VALIDATION_ERRORS = 5
_FORMAT_CHECKER = FormatChecker()


def _path(error: Any) -> str:
    parts = [str(part) for part in error.absolute_path]
    return ".".join(parts) if parts else "$"


def _schema_path(error: Any) -> str:
    parts = [str(part) for part in error.absolute_schema_path]
    return ".".join(parts) if parts else "$"


def _walk_external_references(value: Any, path: str = "$") -> str | None:
    """Return the first forbidden external reference found in a schema.

    Employee schemas are persisted and later evaluated by the API/worker.
    Allowing http(s), file, or other external ``$ref``/``$dynamicRef`` values
    could turn schema validation into an unintended network/filesystem access
    primitive. Local JSON Pointer references (``#...``) remain fully supported.
    """
    if isinstance(value, dict):
        for key in ("$ref", "$dynamicRef"):
            ref = value.get(key)
            if isinstance(ref, str) and not ref.startswith("#"):
                return f"{path}.{key}"
        for key, child in value.items():
            found = _walk_external_references(child, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _walk_external_references(child, f"{path}[{index}]")
            if found:
                return found
    return None


def validate_schema_definition(schema: dict[str, Any], *, field_name: str) -> None:
    """Validate that an Employee schema is a valid local Draft 2020-12 schema."""
    if not isinstance(schema, dict):
        raise ValidationAppError(
            f"Invalid {field_name}: schema must be a JSON object",
            details={"field": field_name, "schema_error": "schema must be an object"},
        )

    external_ref_path = _walk_external_references(schema)
    if external_ref_path:
        raise ValidationAppError(
            f"Invalid {field_name}: external schema references are not allowed",
            details={
                "field": field_name,
                "schema_error": "external $ref/$dynamicRef is not allowed",
                "path": external_ref_path,
            },
        )

    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ValidationAppError(
            f"Invalid {field_name}: {exc.message}",
            details={"field": field_name, "schema_error": exc.message},
        ) from exc


def validate_json_data(
    data: Any,
    schema: dict[str, Any],
    *,
    field_name: str,
) -> None:
    """Validate runtime data against an Employee Draft 2020-12 JSON Schema.

    Up to five deterministic validation errors are returned. This gives API
    callers enough information to correct a payload without allowing an
    unbounded validation-error list to enter API responses or Run error data.
    ``format`` assertions are enabled through jsonschema's FormatChecker.
    """
    validate_schema_definition(schema, field_name=f"{field_name}_schema")
    validator = Draft202012Validator(schema, format_checker=_FORMAT_CHECKER)
    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: (list(error.absolute_path), list(error.absolute_schema_path)),
    )
    if not errors:
        return

    first = errors[0]
    details: dict[str, Any] = {
        "field": field_name,
        "path": _path(first),
        "schema_path": _schema_path(first),
        "validator": first.validator,
        "message": first.message,
        "validation_version": VALIDATION_VERSION,
    }
    if len(errors) > 1:
        details["error_count"] = len(errors)
        details["errors"] = [
            {
                "path": _path(error),
                "schema_path": _schema_path(error),
                "validator": error.validator,
                "message": error.message,
            }
            for error in errors[:_MAX_VALIDATION_ERRORS]
        ]

    raise ValidationAppError(
        f"{field_name} failed JSON Schema validation at {_path(first)}: {first.message}",
        details=details,
    )
