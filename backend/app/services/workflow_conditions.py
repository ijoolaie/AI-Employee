"""Deterministic workflow condition evaluation."""
from __future__ import annotations
from typing import Any
from app.core.exceptions import ValidationAppError

def _lookup_path(context: dict[str, Any], path: str) -> Any:
    if not path.startswith("$."):
        raise ValidationAppError(f"Unsupported context path: {path}")
    value: Any = context
    for part in path[2:].split('.'):
        if not part:
            continue
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def evaluate_condition(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    """Evaluate one deterministic condition against workflow context."""
    op = condition.get("operator", "equals")
    left = _lookup_path(context, str(condition.get("path", "")))
    exists = left is not None
    if op == "exists":
        return exists
    right = condition.get("value")
    if op == "equals": return left == right
    if op == "not_equals": return left != right
    if op == "contains":
        return right in left if isinstance(left, (str, list, tuple, set, dict)) else False
    if op == "gt": return exists and left > right
    if op == "gte": return exists and left >= right
    if op == "lt": return exists and left < right
    if op == "lte": return exists and left <= right
    if op == "in": return exists and left in right
    raise ValidationAppError(f"Unsupported condition operator: {op}")
