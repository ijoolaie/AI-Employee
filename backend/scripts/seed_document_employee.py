"""Seed the Phase 5 system Employee: Document Employee (03_Roadmap_v1.1 §8).

Idempotent: safe to run multiple times. Follows the same manual-script
convention as scripts/seed_report_employee.py and
scripts/promote_platform_admin.py — System Employees (tenant_id NULL) are
seeded by the platform team, not created through the tenant-facing
Employees API (see app/api/v1/employees.py docstring).

Usage (from backend/, with the venv active and DATABASE_URL configured):

    python scripts/seed_document_employee.py

What this creates:
- Employee(slug="document-employee", tenant_id=NULL, kind="system")
- EmployeeVersion(version_number=1, is_current=True) wired to the
  `analyze_document` Tool (app/ai/tool_registry.py) and a prompt template
  that instructs the model to call it, then narrate/summarize the
  document (contract/letter/form/administrative document) in the Run's
  input language.

This script only performs a data seed; it intentionally does not require
its own Alembic migration since it writes rows into tables that already
exist (employees, employee_versions).
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.employee import Employee, EmployeeVersion

SLUG = "document-employee"

PROMPT_TEMPLATE = """You are the Document Employee, a specialized AI Employee for the AI \
Employee Platform (Phase 5 of the Roadmap: "Document Employee" — OCR, PDF \
processing, contracts, letters, forms, and administrative documents).

The user has supplied a `file_id` referencing a previously-uploaded PDF, \
image (PNG/JPEG), or DOCX file (see Input below). Your job:

1. Call the `analyze_document` tool exactly once with that `file_id`.
2. Read the extracted text, detected document type (contract / letter / \
   form / administrative_document), detected fields (dates, amounts, \
   emails, phone numbers, ID-number candidates), and page/OCR info it \
   returns.
3. Write a clear report in the same language as the document (or the \
   user's input language if the document itself is ambiguous). Include: \
   what kind of document this is, a plain-language summary of its content, \
   the key dates/amounts/parties/fields you found, and — if it looks like \
   a contract or form — anything that seems to require action or a \
   signature. Ground every fact ONLY in the tool's output; never invent a \
   date, amount, or clause that was not in the extracted text.
4. If `ocr_pages_used` is greater than 0, mention that some pages required \
   OCR and that extraction quality may vary for low-quality scans.
5. End your answer with a line listing the extracted text file exactly as \
   returned by the tool, in this literal format so the platform UI can \
   offer a download:
   Extracted text: <extracted_text_file_id>

Input:
{input_json}
"""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "file_id": {
            "type": "string",
            "format": "uuid",
            "description": "ID of a PDF/image/DOCX file previously uploaded via POST /api/v1/files",
        }
    },
    "required": ["file_id"],
    "additionalProperties": False,
}

# additionalProperties intentionally omitted (defaults to allowed) so the
# whitelisted `document_artifacts` carry-through in run_service.py
# validates cleanly alongside the always-present `text` field.
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "document_artifacts": {
            "type": "object",
            "properties": {
                "extracted_text_file_id": {"type": "string"},
            },
        },
    },
    "required": ["text"],
}

ALLOWED_TOOLS = ["analyze_document"]


async def seed(db: AsyncSession) -> None:
    result = await db.execute(
        select(Employee).where(Employee.tenant_id.is_(None), Employee.slug == SLUG)
    )
    employee = result.scalar_one_or_none()
    if employee is None:
        employee = Employee(
            tenant_id=None,
            slug=SLUG,
            name="Document Employee",
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
        print("Current EmployeeVersion already matches Phase 5 definition; nothing to do.")
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
