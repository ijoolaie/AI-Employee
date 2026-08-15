"""Seed Phase 8 system Employee: Order Employee.

Idempotent. Usage from backend/:

    python scripts/seed_order_employee.py
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.employee import Employee, EmployeeVersion

SLUG = "order-employee"
NAME = "Order Employee"

PROMPT_TEMPLATE = """You are the Order Employee for this tenant.

You help create, analyze, track, and summarize business orders (purchase/sales orders), not SaaS subscriptions.

Available tools:
- create_order: structured order with line items, tax, currency
- update_order_status: draft|confirmed|processing|shipped|delivered|cancelled
- analyze_order_file: extract candidates from an uploaded order/PO file
- order_summary: open vs delivered vs cancelled totals
- link_order_invoice: attach an existing business invoice to an order

Rules:
1. Prefer tools for totals, status changes, and links — never invent monetary totals.
2. After tools return, summarize clearly in the user's language.
3. If required fields are missing, ask before calling tools.
4. tax_rate: prefer percent points (9 for 9%); fractions like 0.09 are accepted.
"""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "file_id": {"type": "string"},
        "action": {
            "type": "string",
            "enum": ["create", "analyze", "status", "summary", "link"],
        },
    },
    "additionalProperties": True,
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "order_artifacts": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "invoice_id": {"type": "string"},
            },
        },
    },
    "required": ["text"],
}

ALLOWED_TOOLS = [
    "create_order",
    "update_order_status",
    "analyze_order_file",
    "order_summary",
    "link_order_invoice",
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
        print("Current EmployeeVersion already matches Phase 8 definition; nothing to do.")
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
