"""Compatibility facade for automatic run-memory extraction.

The implementation remains in ``auto_extract_impl``.  This module preserves
legacy imports while accepting the run-shaped call used by the run service.
"""
from __future__ import annotations

from typing import Any

from app.memory.auto_extract_impl import _find_duplicate, _parse_candidates
from app.memory.auto_extract_impl import auto_memory_settings as _auto_memory_settings
from app.memory.auto_extract_impl import extract_and_consolidate_run_memory as _extract


def auto_memory_settings(rules: dict[str, Any]) -> dict[str, Any]:
    return _auto_memory_settings(rules)


async def extract_and_consolidate_run_memory(
    db,
    *,
    run=None,
    output_data: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
    tenant_id=None,
    employee_id=None,
    run_id=None,
    input_data: dict[str, Any] | None = None,
    output_text: str | None = None,
    rules: dict[str, Any] | None = None,
) -> dict[str, int]:
    """Accept both the legacy run-shaped call and the canonical arguments."""
    if run is not None:
        tenant_id = run.tenant_id
        employee_id = run.employee_id
        run_id = run.id
        input_data = run.input_data or {}
    if output_data is not None and output_text is None:
        output_text = str(output_data.get("content", ""))
    if output_text is None:
        output_text = ""
    if rules is None:
        rules = {"memory": settings or {}}
    return await _extract(
        db,
        tenant_id=tenant_id,
        employee_id=employee_id,
        run_id=run_id,
        input_data=input_data or {},
        output_text=output_text,
        rules=rules,
    )
