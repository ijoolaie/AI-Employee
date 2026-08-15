"""Seed the Phase 2 system Employee: Report Employee (03_Roadmap_v1.1 §5).

Idempotent: safe to run multiple times. Follows the same manual-script
convention as scripts/promote_platform_admin.py — System Employees
(tenant_id NULL) are seeded by the platform team, not created through the
tenant-facing Employees API (see app/api/v1/employees.py docstring).

Usage (from backend/, with the venv active and DATABASE_URL configured):

    python scripts/seed_report_employee.py

What this creates:
- Employee(slug="report-employee", tenant_id=NULL, kind="system")
- EmployeeVersion(version_number=1, is_current=True) wired to the
  `analyze_dataset` Tool (app/ai/tool_registry.py) and a prompt template
  that instructs the model to call it, then narrate KPIs/insights in the
  Run's input language.

This script only performs a data seed; it intentionally does not require
its own Alembic migration since it writes rows into tables that already
exist as of v0.2.47 (employees, employee_versions).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Support both ``python -m scripts.seed_report_employee`` and the direct
# ``python scripts/seed_report_employee.py`` form used in Docker/debugging.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.employee import Employee, EmployeeVersion

SLUG = "report-employee"

PROMPT_TEMPLATE = """You are the Report Employee, a specialized AI Employee for the AI Employee \
Platform (Phase 2 of the Roadmap: "Report Employee").

The user has supplied a `file_id` referencing a previously-uploaded CSV or \
Excel file (see Input below). Your job:

1. Call the `analyze_dataset` tool exactly once with that `file_id`.
2. Read the KPIs, category breakdown, and forecast (if present) it returns.
3. Write a clear, business-friendly report in the same language as the \
   user's input. Include: a short executive summary, the key KPIs, notable \
   category patterns, the forecast/trend if one was computed, and 2-4 \
   concrete recommendations grounded ONLY in the numbers returned by the \
   tool — never invent figures that did not come from the tool result.
4. End your answer with a line listing the generated report files exactly \
   as returned by the tool, in this literal format so the platform UI can \
   offer downloads:
   PDF: <pdf_file_id>
   Excel: <excel_file_id>

Input:
{input_json}
"""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "file_id": {
            "type": "string",
            "format": "uuid",
            "description": "ID of a CSV/Excel file previously uploaded via POST /api/v1/files",
        }
    },
    "required": ["file_id"],
    "additionalProperties": False,
}

# additionalProperties intentionally omitted (defaults to allowed) so the
# whitelisted `report_artifacts` carry-through in run_service.py validates
# cleanly alongside the always-present `text` field.
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "report_artifacts": {
            "type": "object",
            "properties": {
                "pdf_file_id": {"type": "string"},
                "excel_file_id": {"type": "string"},
                "chart_file_ids": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    "required": ["text"],
}

ALLOWED_TOOLS = ["analyze_dataset"]


async def seed(db: AsyncSession) -> None:
    result = await db.execute(
        select(Employee).where(Employee.tenant_id.is_(None), Employee.slug == SLUG)
    )
    employee = result.scalar_one_or_none()
    if employee is None:
        employee = Employee(
            tenant_id=None,
            slug=SLUG,
            name="Report Employee",
            kind="system",
            is_active=True,
        )
        db.add(employee)
        await db.flush()
        print(f"Created Employee {employee.id} ({SLUG})")
    else:
        print(f"Employee already exists: {employee.id} ({SLUG})")

    result = await db.execute(
        select(EmployeeVersion).where(
            EmployeeVersion.employee_id == employee.id, EmployeeVersion.is_current.is_(True)
        )
    )
    current = result.scalar_one_or_none()
    if current is not None:
        current_matches = (
            current.input_schema == INPUT_SCHEMA
            and current.output_schema == OUTPUT_SCHEMA
            and current.prompt_template == PROMPT_TEMPLATE
            and current.allowed_tools == ALLOWED_TOOLS
            and current.rules == {}
        )
        if current_matches:
            print("Current EmployeeVersion already matches Phase 2 definition; nothing to do.")
            await db.commit()
            return

    result = await db.execute(
        select(EmployeeVersion).where(EmployeeVersion.employee_id == employee.id)
    )
    existing_versions = list(result.scalars().all())
    next_version_number = (max((v.version_number for v in existing_versions), default=0)) + 1

    if current is not None:
        current.is_current = False

    version = EmployeeVersion(
        employee_id=employee.id,
        version_number=next_version_number,
        is_current=True,
        input_schema=INPUT_SCHEMA,
        output_schema=OUTPUT_SCHEMA,
        prompt_template=PROMPT_TEMPLATE,
        allowed_tools=ALLOWED_TOOLS,
        rules={},
    )
    db.add(version)
    await db.commit()
    print(f"Published EmployeeVersion {next_version_number} for {SLUG}")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
