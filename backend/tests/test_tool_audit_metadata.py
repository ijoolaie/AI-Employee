from app.services.tool_audit_metadata import tool_result_audit_summary


def test_analyze_dataset_audit_summary_keeps_verification_metrics_only():
    result = {
        "row_count": 23,
        "column_count": 3,
        "columns": ["customer_email", "product", "unit_price"],
        "numeric_summary": {"unit_price": {"sum": 2875, "mean": 125}},
        "category_summary": {"customer_email": {"alice@example.test": 1}},
        "forecast": {"trend": "increasing", "next_periods_forecast": [10, 11, 12]},
        "product_revenue": {
            "products": [
                {"product": "Secret customer product", "units_sold": 23, "revenue": 2800}
            ],
            "total_units_sold": 23,
            "total_revenue": 2800,
        },
        "report_artifacts": {
            "pdf_file_id": "pdf-id",
            "excel_file_id": "excel-id",
            "chart_file_ids": ["chart-1", "chart-2"],
        },
    }

    summary = tool_result_audit_summary("analyze_dataset", result)

    assert summary == {
        "result_summary": {
            "row_count": 23,
            "column_count": 3,
            "forecast_available": True,
            "artifact_count": 4,
            "total_units_sold": 23,
            "total_revenue": 2800,
            "product_count": 1,
            "forecast_trend": "increasing",
        }
    }
    serialized = str(summary)
    assert "customer_email" not in serialized
    assert "alice@example.test" not in serialized
    assert "Secret customer product" not in serialized
    assert "pdf-id" not in serialized


def test_tool_result_audit_summary_fails_closed_for_unknown_or_malformed_results():
    assert tool_result_audit_summary("send_email", {"to": ["alice@example.test"]}) == {}
    assert tool_result_audit_summary("analyze_dataset", "raw output") == {}
    assert tool_result_audit_summary("analyze_dataset", {"row_count": -3, "column_count": True}) == {
        "result_summary": {"forecast_available": False}
    }
