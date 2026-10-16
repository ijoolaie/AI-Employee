"""Source-contract tests for Report Analyst artifact reuse.

The complete path uses PostgreSQL advisory locks and tenant-scoped FileObjects;
these tests guard the key idempotency and cache-validation invariants without
requiring a live database.
"""


def test_report_analysis_serializes_same_source_and_checks_existing_artifacts():
    from pathlib import Path

    source = (Path(__file__).parents[1] / "app/modules/employees/report/service.py").read_text(encoding="utf-8")

    assert "pg_advisory_xact_lock(lock_key)" in source
    assert "async def _existing_report_artifacts(" in source
    assert 'AuditLog.action == "report.generated"' in source
    assert 'metadata.get("chart_file_ids")' in source
    assert "FileObject.tenant_id == tenant_id" in source
    assert 'FileObject.status == "active"' in source
    assert 'action="report.reused"' in source


def test_report_generation_persists_chart_ids_for_future_idempotent_reuse():
    from pathlib import Path

    source = (Path(__file__).parents[1] / "app/modules/employees/report/service.py").read_text(encoding="utf-8")

    assert '"chart_file_ids": chart_file_ids' in source
    assert '"pdf_file_id": str(pdf_file.id)' in source
    assert '"excel_file_id": str(excel_file.id)' in source
