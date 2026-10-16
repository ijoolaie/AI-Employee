"""Safe, bounded summaries of tool results for durable audit metadata.

Audit events should support operational verification without duplicating raw
customer datasets, tool arguments, or full tool outputs.
"""
from __future__ import annotations

from typing import Any


def tool_result_audit_summary(tool_name: str, result: Any) -> dict[str, Any]:
    """Return an allowlisted summary for known result shapes, never raw payloads."""
    if tool_name != "analyze_dataset" or not isinstance(result, dict):
        return {}

    summary: dict[str, Any] = {}
    for key in ("row_count", "column_count"):
        value = result.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            summary[key] = value

    summary["forecast_available"] = isinstance(result.get("forecast"), dict)
    artifacts = result.get("report_artifacts")
    if isinstance(artifacts, dict):
        chart_ids = artifacts.get("chart_file_ids")
        summary["artifact_count"] = (
            int(isinstance(artifacts.get("pdf_file_id"), str) and bool(artifacts.get("pdf_file_id")))
            + int(isinstance(artifacts.get("excel_file_id"), str) and bool(artifacts.get("excel_file_id")))
            + (len(chart_ids) if isinstance(chart_ids, list) else 0)
        )

    sales = result.get("product_revenue")
    if isinstance(sales, dict):
        for key in ("total_units_sold", "total_revenue"):
            value = sales.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                summary[key] = value
        products = sales.get("products")
        if isinstance(products, list):
            summary["product_count"] = len(products)

    forecast = result.get("forecast")
    if isinstance(forecast, dict) and forecast.get("trend") in {"increasing", "decreasing", "flat"}:
        summary["forecast_trend"] = forecast["trend"]

    return {"result_summary": summary} if summary else {}
