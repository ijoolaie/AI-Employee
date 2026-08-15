"""Phase 2 — Report Employee analysis-engine unit tests.

Dependency-light by design (same rationale as test_rbac.py): these exercise
the pure computation/rendering functions in app.services.report_service
directly, with an in-memory DataFrame, so they run without PostgreSQL/Redis.
The DB-backed path (analyze_dataset() end-to-end: FileObject read/write via
Object Storage, audit_service.record) is NOT exercised here and remains
environment-dependent like the rest of the v0.2.x suite — see
documents/58_PHASE_2_REPORT_EMPLOYEE_AS_BUILT_v0.3.0.md verification boundary.
"""

import pandas as pd
import pytest

from app.core.exceptions import ValidationAppError
from app.services import report_service


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=6, freq="D"),
            "region": ["North", "South", "North", "East", "South", "North"],
            "revenue": [100.0, 200.0, 150.0, 300.0, 250.0, 400.0],
        }
    )


def test_compute_kpis_returns_numeric_and_category_summaries():
    kpis = report_service._compute_kpis(_sample_df())
    assert kpis["row_count"] == 6
    assert "revenue" in kpis["numeric_summary"]
    assert kpis["numeric_summary"]["revenue"]["sum"] == pytest.approx(1400.0)
    assert "region" in kpis["category_summary"]
    assert kpis["category_summary"]["region"]["North"] == 3


def test_simple_forecast_detects_increasing_trend():
    forecast = report_service._simple_forecast(_sample_df())
    assert forecast is not None
    assert forecast["value_column"] == "revenue"
    assert forecast["trend"] == "increasing"
    assert len(forecast["next_periods_forecast"]) == 3


def test_simple_forecast_returns_none_without_date_column():
    df = pd.DataFrame({"region": ["North", "South"], "revenue": [1.0, 2.0]})
    assert report_service._simple_forecast(df) is None


def test_read_dataframe_rejects_empty_file():
    with pytest.raises(ValidationAppError):
        report_service._read_dataframe(b"col_a,col_b\n", "empty.csv", "text/csv")


def test_read_dataframe_rejects_unparseable_bytes():
    with pytest.raises(ValidationAppError):
        report_service._read_dataframe(b"\x00\x01\x02not,a,csv", "broken.xlsx", None)


def test_render_charts_produces_png_bytes_for_numeric_columns():
    charts = report_service._render_charts(_sample_df())
    assert len(charts) >= 1
    name, data = charts[0]
    assert name.endswith(".png")
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_excel_produces_workbook_bytes():
    df = _sample_df()
    kpis = report_service._compute_kpis(df)
    excel_bytes = report_service._render_excel(df, kpis)
    # XLSX files are zip containers — assert the zip magic number, not full parse.
    assert excel_bytes[:2] == b"PK"


def test_render_pdf_produces_pdf_bytes():
    df = _sample_df()
    kpis = report_service._compute_kpis(df)
    forecast = report_service._simple_forecast(df)
    charts = report_service._render_charts(df)
    pdf_bytes = report_service._render_pdf(
        source_filename="sample.csv", kpis=kpis, forecast=forecast, charts=charts
    )
    assert pdf_bytes[:5] == b"%PDF-"
