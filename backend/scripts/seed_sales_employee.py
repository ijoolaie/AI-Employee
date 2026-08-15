"""Seed Phase 9 system Employee: Sales Employee."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.employee import Employee, EmployeeVersion

SLUG = "sales-employee"
NAME = "Sales Employee"

PROMPT_TEMPLATE = """You are the Sales Employee for this tenant.

You help with lightweight CRM: create and advance deals, pipeline overview, and a simple revenue forecast.

Available tools:
- create_deal: title, customer, amount, stage, probability
- update_deal_stage: lead|qualified|proposal|negotiation|won|lost
- sales_pipeline_summary: counts and amounts by stage + weighted pipeline
- sales_forecast: probability-weighted open deals within horizon_days

Rules:
1. Prefer tools for numbers and stages — do not invent pipeline totals.
2. After tools return, summarize clearly in the user's language.
3. Default stage is lead; default probability follows stage if omitted.
4. Forecast method is deliberately simple and auditable (weighted open deals).
"""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "action": {
            "type": "string",
            "enum": ["create", "stage", "pipeline", "forecast"],
        },
    },
    "additionalProperties": True,
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "sales_artifacts": {
            "type": "object",
            "properties": {
                "deal_id": {"type": "string"},
            },
        },
    },
    "required": ["text"],
}

ALLOWED_TOOLS = [
    "create_deal",
    "update_deal_stage",
    "sales_pipeline_summary",
    "sales_forecast",
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
        print("Current EmployeeVersion already matches Phase 9 definition; nothing to do.")
        await db.commit()
        return

    result = await db.execute(
        select(EmployeeVersion).where(EmployeeVersion.employee_id == employee.id)
    )
    existing = list(result.scalars().all())
    next_v = (max((v.version_number for v in existing), default=0)) + 1
    if current is not None:
        current.is_current = False

    version = EmployeeVersion(
        employee_id=employee.id,
        version_number=next_v,
        is_current=True,
        input_schema=INPUT_SCHEMA,
        output_schema=OUTPUT_SCHEMA,
        prompt_template=PROMPT_TEMPLATE,
        allowed_tools=ALLOWED_TOOLS,
        rules={},
    )
    db.add(version)
    await db.commit()
    print(f"Published EmployeeVersion {next_v} for {SLUG}")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
