"""Compatibility facade for the modular Report Employee service."""
from app.modules.employees.report.service import *  # noqa: F401,F403
from app.modules.employees.report.service import (  # noqa: F401
    MAX_ROWS,
    MAX_CHART_COLUMNS,
    MAX_EXCEL_EXPORT_ROWS,
    _compute_kpis,
    _read_dataframe,
    _render_charts,
    _render_excel,
    _render_pdf,
    _simple_forecast,
)
