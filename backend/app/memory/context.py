"""Employee memory execution policy and query construction."""
from __future__ import annotations
import json
from typing import Any
from app.core.exceptions import ValidationAppError

def memory_settings(rules: dict[str, Any]) -> dict[str, Any]:
    raw = rules.get("memory", {}) if isinstance(rules, dict) else {}
    if not isinstance(raw, dict) or not raw.get("enabled", False):
        return {"enabled": False, "top_k": 0, "query_fields": [], "min_score": 0.0}
    fields = raw.get("query_fields", [])
    if not isinstance(fields, list) or not fields or any(not isinstance(v, str) or not v.strip() for v in fields):
        raise ValidationAppError("Employee memory requires a non-empty query_fields list of strings")
    fields = list(dict.fromkeys(v.strip() for v in fields))
    top_k = raw.get("top_k", 5)
    if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 20:
        raise ValidationAppError("Employee memory top_k must be between 1 and 20")
    min_score = raw.get("min_score", 0.35)
    if not isinstance(min_score, (int, float)) or isinstance(min_score, bool) or not 0.0 <= float(min_score) <= 1.0:
        raise ValidationAppError("Employee memory min_score must be between 0 and 1")
    return {"enabled": True, "top_k": top_k, "query_fields": fields, "min_score": float(min_score)}

def build_memory_query(input_data: dict[str, Any], query_fields: list[str]) -> str:
    selected = {key: input_data[key] for key in query_fields if key in input_data}
    if not selected:
        raise ValidationAppError("Employee memory query_fields did not match any Run input fields", details={"query_fields": query_fields})
    return json.dumps(selected, ensure_ascii=False, sort_keys=True, default=str)[:8000]
