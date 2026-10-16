import asyncio
import io
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.modules.employees.report import service as report_service


def _query_result(values):
    return SimpleNamespace(
        scalars=lambda: SimpleNamespace(all=lambda: values)
    )


def test_analyze_dataset_reuses_existing_active_artifacts(monkeypatch):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    source_id = uuid.uuid4()
    pdf_id = uuid.uuid4()
    excel_id = uuid.uuid4()
    chart_id = uuid.uuid4()

    source_file = SimpleNamespace(
        id=source_id,
        storage_key="tenant/source.csv",
        filename="sales.csv",
        content_type="text/csv",
    )

    existing_audit = SimpleNamespace(
        metadata_={
            "pdf_file_id": str(pdf_id),
            "excel_file_id": str(excel_id),
            "chart_file_ids": [str(chart_id)],
        }
    )

    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            MagicMock(),  # PostgreSQL advisory-lock statement
            _query_result([existing_audit]),
            _query_result([pdf_id, excel_id, chart_id]),
        ]
    )

    monkeypatch.setattr(
        report_service.file_service,
        "get_file",
        AsyncMock(return_value=source_file),
    )

    backend = MagicMock()
    backend.open.return_value = io.BytesIO(
        b"date,region,revenue\n"
        b"2026-01-01,North,100\n"
        b"2026-01-02,South,200\n"
    )
    monkeypatch.setattr(
        report_service.storage,
        "get_storage_backend",
        lambda: backend,
    )

    audit_record = AsyncMock()
    monkeypatch.setattr(
        report_service.audit_service,
        "record",
        audit_record,
    )

    render_charts = MagicMock(side_effect=AssertionError("charts regenerated"))
    render_pdf = MagicMock(side_effect=AssertionError("PDF regenerated"))
    render_excel = MagicMock(side_effect=AssertionError("Excel regenerated"))
    save_file = AsyncMock(side_effect=AssertionError("file saved again"))

    monkeypatch.setattr(report_service, "_render_charts", render_charts)
    monkeypatch.setattr(report_service, "_render_pdf", render_pdf)
    monkeypatch.setattr(report_service, "_render_excel", render_excel)
    monkeypatch.setattr(report_service, "_save_generated_file", save_file)

    result = asyncio.run(
        report_service.analyze_dataset(
            db,
            tenant_id=tenant_id,
            actor_id=actor_id,
            file_id=str(source_id),
        )
    )

    assert result["report_artifacts"] == {
        "pdf_file_id": str(pdf_id),
        "excel_file_id": str(excel_id),
        "chart_file_ids": [str(chart_id)],
    }

    audit_record.assert_awaited_once()
    assert audit_record.await_args.kwargs["action"] == "report.reused"
    assert audit_record.await_args.kwargs["metadata"]["artifact_count"] == 3

    render_charts.assert_not_called()
    render_pdf.assert_not_called()
    render_excel.assert_not_called()
    save_file.assert_not_awaited()
