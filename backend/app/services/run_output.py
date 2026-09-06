"""Helpers for normalizing model output to Employee output schemas."""
from __future__ import annotations

from typing import Any


def build_output_data(content: str, output_schema: dict[str, Any]) -> dict[str, Any]:
    """Map the provider's text result onto the Employee's declared text field.

    Employee output contracts use ``text`` as the canonical natural-language
    result field. ``content`` is retained only for legacy schemas that
    explicitly declare it.
    """
    properties = output_schema.get("properties") or {}
    if "text" in properties:
        return {"text": content}
    if "content" in properties:
        return {"content": content}
    return {"content": content}
