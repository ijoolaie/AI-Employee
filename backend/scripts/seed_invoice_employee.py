"""Seed Phase 7 system Employee: Invoice Employee.

Idempotent. Usage from backend/:

    python scripts/seed_invoice_employee.py
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.employee import Employee, EmployeeVersion

SLUG = "invoice-employee"
NAME = "Invoice Employee"

PROMPT_TEMPLATE = """You are the Invoice Employee for this tenant.

You help create, analyze, track, and export business invoices (NOT SaaS subscription billing).

Available tools:
- create_invoice: structured invoice with line items, tax, currency
- update_invoice_status: draft|sent|paid|overdue|void
- analyze_invoice_file: extract candidates from an uploaded invoice file
- export_invoice_pdf: render PDF and store as a tenant file
- invoice_financial_summary: outstanding vs collected totals

Rules:
1. Prefer tools for any numeric total, status change, or PDF export — never invent totals.
2. After tools return, summarize clearly in the user's language.
3. If required fields are missing, ask for them before calling tools.
"""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "file_id": {"type": "string"},
        "action": {
            "type": "string",
            "enum": ["create", "analyze", "status", "export", "summary"],
        },
    },
    "additionalProperties": True,
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "invoice_artifacts": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string"},
                "pdf_file_id": {"type": "string"},
            },
        },
    },
    "required": ["text"],
}

ALLOWED_TOOLS = [
    "create_invoice",
    "update_invoice_status",
    "analyze_invoice_file",
    "export_invoice_pdf",
    "invoice_financial_summary",
]


async def seed(db: AsyncSession) -> None:
    result = await db.execute(
        select(Employee).where(Employee.tenant_id.is_(None), Employee.slug == SLUG)
    )
    employee = result.scalar_one_or_none()
    if employee is None:
        employee = Employee(
            tenant_id=None,
            slug=SLUG,
            name=NAME,
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
    if current is not None and current.allowed_tools == ALLOWED_TOOLS:
        print("Current EmployeeVersion already matches Phase 7 definition; nothing to do.")
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
