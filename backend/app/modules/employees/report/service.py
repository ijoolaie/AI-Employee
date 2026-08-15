"""Report Employee dataset analysis engine (Phase 2 — 03_Roadmap §5).

Given a previously-uploaded tenant file (CSV or Excel), this module computes
descriptive KPIs, generates chart images, produces a simple linear-trend
forecast when a date-like + numeric column pair is present, and renders a
PDF + Excel report. Every output artifact is persisted through the existing
Object Storage abstraction (app.services.storage) and registered as a
tenant-scoped FileObject via app.services.file_service — no new storage or
tenant-isolation surface is introduced; report artifacts are downloadable
through the standard Files API exactly like any uploaded file.

This module is invoked exclusively through the `analyze_dataset` Tool
(app.ai.tool_registry), which enforces tenant scoping, the `run.execute`
permission, and JSON-Schema argument validation before calling here. It is
never reachable directly from a route.

Deliberately in-scope for the Phase 2 "Report Employee" exit criteria
(03_Roadmap_v1.1 §5): تحلیل داده، نمودار، گزارش مدیریتی، KPI، پیش‌بینی ساده،
PDF/Excel output. Text summarization/insight narration is produced by the
calling model (via the Employee prompt), not by this module — this module
only computes the deterministic, auditable numeric/graphical substrate the
model reasons over, so KPI numbers in the final report can never be an LLM
hallucination.
"""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationAppError
from app.models.file import FileObject
from app.services import audit_service, file_service, storage

# Bounds keep a single Tool call CPU/memory-bounded on a shared worker
# (12_Workflow_Engine / 14_Security cost & abuse-limit principles).
MAX_ROWS = 200_000
MAX_CHART_COLUMNS = 3
MAX_EXCEL_EXPORT_ROWS = 5000


def _read_dataframe(raw: bytes, filename: str, content_type: str | None) -> pd.DataFrame:
    name = (filename or "").lower()
    is_excel = name.endswith((".xlsx", ".xls")) or (content_type or "") in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    )
    buf = io.BytesIO(raw)
    try:
        if is_excel:
            df = pd.read_excel(buf)
        else:
            # CSV uploads created by Windows/Excel are commonly encoded as
            # cp1252 rather than UTF-8. Try common encodings in order.
            last_exc: Exception | None = None
            for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
                try:
                    buf.seek(0)
                    df = pd.read_csv(buf, encoding=encoding)
                    break
                except UnicodeDecodeError as exc:
                    last_exc = exc
            else:
                raise last_exc or ValueError("Unable to decode CSV")
    except Exception as exc:  # noqa: BLE001 — normalize any parser failure
        raise ValidationAppError(
            "Could not parse file as CSV/Excel tabular data",
            details={"filename": filename, "error": str(exc)[:300]},
        ) from exc
    if df.empty:
        raise ValidationAppError("Uploaded file contains no data rows")
    if len(df) > MAX_ROWS:
        df = df.head(MAX_ROWS)
    return df


def _compute_kpis(df: pd.DataFrame) -> dict[str, Any]:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = [c for c in df.columns if c not in numeric_cols]

    numeric_summary: dict[str, Any] = {}
    for col in numeric_cols[:10]:
        series = df[col].dropna()
        if series.empty:
            continue
        numeric_summary[str(col)] = {
            "sum": float(series.sum()),
            "mean": float(series.mean()),
            "min": float(series.min()),
            "max": float(series.max()),
            "missing": int(df[col].isna().sum()),
        }

    category_summary: dict[str, Any] = {}
    for col in categorical_cols[:5]:
        counts = df[col].astype(str).value_counts().head(5)
        category_summary[str(col)] = {str(k): int(v) for k, v in counts.items()}

    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": [str(c) for c in df.columns],
        "numeric_summary": numeric_summary,
        "category_summary": category_summary,
    }


def _simple_forecast(df: pd.DataFrame) -> dict[str, Any] | None:
    """Best-effort linear-trend forecast for the first date-like + numeric
    column pair (Roadmap §5 "پیش‌بینی ساده"). Returns None when no suitable
    column pair exists — this is a deliberately minimal Phase 2 forecast,
    not a general time-series model."""
    date_col = None
    for col in df.columns:
        label = str(col).lower()
        if "date" in label or "تاریخ" in str(col):
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
            except Exception:  # noqa: BLE001
                continue
            if parsed.notna().sum() >= max(3, int(len(df) * 0.5)):
                date_col = col
                break
    if date_col is None:
        return None

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        return None
    value_col = numeric_cols[0]

    work = df[[date_col, value_col]].copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    work = work.dropna().sort_values(date_col)
    if len(work) < 3:
        return None

    import numpy as np

    x = np.arange(len(work))
    y = work[value_col].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    next_periods = 3
    forecast_values = [
        float(slope * (len(work) - 1 + i) + intercept) for i in range(1, next_periods + 1)
    ]
    return {
        "date_column": str(date_col),
        "value_column": str(value_col),
        "trend": "increasing" if slope > 0 else ("decreasing" if slope < 0 else "flat"),
        "next_periods_forecast": forecast_values,
    }


def _render_charts(df: pd.DataFrame) -> list[tuple[str, bytes]]:
    import matplotlib

    matplotlib.use("Agg")  # headless — this runs inside a Celery/API worker, never a display
    import matplotlib.pyplot as plt

    numeric_cols = df.select_dtypes(include="number").columns.tolist()[:MAX_CHART_COLUMNS]
    charts: list[tuple[str, bytes]] = []

    for col in numeric_cols:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        series = df[col].dropna()
        if len(series) > 200:
            series = series.iloc[:200]
        series.reset_index(drop=True).plot(kind="line", ax=ax, color="#2563eb")
        ax.set_title(str(col))
        ax.set_xlabel("Row")
        ax.set_ylabel(str(col))
        fig.tight_layout()
        out = io.BytesIO()
        fig.savefig(out, format="png", dpi=110)
        plt.close(fig)
        charts.append((f"chart_{col}.png", out.getvalue()))

    categorical_cols = [c for c in df.columns if c not in df.select_dtypes(include="number").columns]
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        val_col = numeric_cols[0]
        grouped = df.groupby(cat_col)[val_col].sum().sort_values(ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(6, 3.5))
        grouped.plot(kind="bar", ax=ax, color="#16a34a")
        ax.set_title(f"{val_col} by {cat_col}")
        fig.tight_layout()
        out = io.BytesIO()
        fig.savefig(out, format="png", dpi=110)
        plt.close(fig)
        charts.append((f"chart_{cat_col}_by_{val_col}.png", out.getvalue()))

    return charts


def _render_pdf(
    *, source_filename: str, kpis: dict[str, Any], forecast: dict[str, Any] | None,
    charts: list[tuple[str, bytes]],
) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Report Employee — Data Analysis Report", styles["Title"]),
        Paragraph(f"Source: {source_filename}", styles["Normal"]),
        Paragraph(f"Generated: {datetime.now(timezone.utc).isoformat()}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"Rows: {kpis['row_count']} · Columns: {kpis['column_count']}", styles["Normal"]),
        Spacer(1, 12),
    ]

    if kpis["numeric_summary"]:
        story.append(Paragraph("Numeric KPIs", styles["Heading2"]))
        rows = [["Column", "Sum", "Mean", "Min", "Max", "Missing"]]
        for col, s in kpis["numeric_summary"].items():
            rows.append(
                [col, f"{s['sum']:.2f}", f"{s['mean']:.2f}", f"{s['min']:.2f}", f"{s['max']:.2f}", str(s["missing"])]
            )
        table = Table(rows, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 12))

    if forecast:
        story.append(Paragraph("Simple Forecast", styles["Heading2"]))
        forecast_line = ", ".join(f"{v:.2f}" for v in forecast["next_periods_forecast"])
        story.append(
            Paragraph(
                f"Trend for {forecast['value_column']} over {forecast['date_column']}: "
                f"{forecast['trend']}. Next periods: {forecast_line}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 12))

    if charts:
        story.append(Paragraph("Charts", styles["Heading2"]))
        for _name, png_bytes in charts:
            story.append(Image(io.BytesIO(png_bytes), width=16 * cm, height=9.3 * cm))
            story.append(Spacer(1, 8))

    doc.build(story)
    return buf.getvalue()


def _render_excel(df: pd.DataFrame, kpis: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.head(MAX_EXCEL_EXPORT_ROWS).to_excel(writer, sheet_name="Data", index=False)
        summary_rows = [{"column": col, **s} for col, s in kpis["numeric_summary"].items()]
        if summary_rows:
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name="KPI Summary", index=False)
    return buf.getvalue()


async def _save_generated_file(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    filename: str,
    content_type: str,
    data: bytes,
) -> FileObject:
    return await file_service.upload_file(
        db,
        tenant_id=tenant_id,
        uploaded_by=actor_id,
        filename=filename,
        content_type=content_type,
        data=io.BytesIO(data),
    )


async def analyze_dataset(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    file_id: str,
) -> dict[str, Any]:
    """Core Phase 2 entry point, called by the `analyze_dataset` Tool handler.

    tenant_id/actor_id are always resolved server-side from the Run's
    TenantContext (never client-supplied), matching the tenant-isolation
    rule already enforced for `send_email` in app.ai.tool_registry.
    """
    try:
        source_uuid = uuid.UUID(str(file_id))
    except ValueError as exc:
        raise ValidationAppError("file_id must be a valid UUID") from exc

    source_file = await file_service.get_file(db, tenant_id=tenant_id, file_id=source_uuid)
    backend = storage.get_storage_backend()
    with backend.open(source_file.storage_key) as fh:
        raw = fh.read()

    df = _read_dataframe(raw, source_file.filename, source_file.content_type)
    kpis = _compute_kpis(df)
    forecast = _simple_forecast(df)
    charts = _render_charts(df)

    pdf_bytes = _render_pdf(
        source_filename=source_file.filename, kpis=kpis, forecast=forecast, charts=charts
    )
    excel_bytes = _render_excel(df, kpis)

    base_name = source_file.filename.rsplit(".", 1)[0] or "dataset"
    pdf_file = await _save_generated_file(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        filename=f"{base_name}_report.pdf",
        content_type="application/pdf",
        data=pdf_bytes,
    )
    excel_file = await _save_generated_file(
        db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        filename=f"{base_name}_report.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        data=excel_bytes,
    )
    chart_file_ids: list[str] = []
    for chart_name, chart_bytes in charts:
        chart_file = await _save_generated_file(
            db,
            tenant_id=tenant_id,
            actor_id=actor_id,
            filename=f"{base_name}_{chart_name}",
            content_type="image/png",
            data=chart_bytes,
        )
        chart_file_ids.append(str(chart_file.id))

    await audit_service.record(
        db,
        action="report.generated",
        actor_type="system",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_type="file",
        resource_id=str(source_file.id),
        metadata={
            "pdf_file_id": str(pdf_file.id),
            "excel_file_id": str(excel_file.id),
            "chart_count": len(chart_file_ids),
            "row_count": kpis["row_count"],
        },
    )

    return {
        "row_count": kpis["row_count"],
        "column_count": kpis["column_count"],
        "columns": kpis["columns"],
        "numeric_summary": kpis["numeric_summary"],
        "category_summary": kpis["category_summary"],
        "forecast": forecast,
        "report_artifacts": {
            "pdf_file_id": str(pdf_file.id),
            "excel_file_id": str(excel_file.id),
            "chart_file_ids": chart_file_ids,
        },
    }
