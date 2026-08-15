"""Pure helpers for Employee RAG execution policy and query construction."""
from __future__ import annotations

import json
from typing import Any

from app.core.exceptions import ValidationAppError


def rag_settings(rules: dict[str, Any]) -> dict[str, Any]:
    """Normalize the optional EmployeeVersion RAG policy.

    RAG is opt-in. When enabled, query_fields must be explicit so the
    platform never embeds arbitrary Run input by accident.
    """
    raw = rules.get("rag", {}) if isinstance(rules, dict) else {}
    if not isinstance(raw, dict) or not raw.get("enabled", False):
        return {"enabled": False, "top_k": 0, "query_fields": []}

    fields = raw.get("query_fields", [])
    if not isinstance(fields, list) or not fields or any(not isinstance(v, str) or not v.strip() for v in fields):
        raise ValidationAppError(
            "Employee RAG requires a non-empty query_fields list of strings"
        )
    fields = list(dict.fromkeys(v.strip() for v in fields))
    top_k = raw.get("top_k", 5)
    if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 20:
        raise ValidationAppError("Employee RAG top_k must be between 1 and 20")
    return {"enabled": True, "top_k": top_k, "query_fields": fields}


def build_rag_query(input_data: dict[str, Any], query_fields: list[str]) -> str:
    selected = {key: input_data[key] for key in query_fields if key in input_data}
    if not selected:
        raise ValidationAppError(
            "Employee RAG query_fields did not match any Run input fields",
            details={"query_fields": query_fields},
        )
    query = json.dumps(selected, ensure_ascii=False, sort_keys=True, default=str)
    return query[:8000]
