"""Feedback service — Phase 3 "Validation" support (03_Roadmap_v1.1 §6).

See app/models/feedback.py for the scope note: this records feedback and
computes the Roadmap's own Phase 3 exit-criteria proxy metric (>=3 tenants
regularly running the Report Employee). It does not, by itself, decide
that Phase 3 is complete — that judgment call belongs to the product team,
using this data plus the qualitative feedback text.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.employee import Employee
from app.models.feedback import Feedback
from app.models.run import Run
from app.models.tenant import Tenant

# "Regularly using" proxy, per Roadmap §6 ("مشتری‌های فعال ... به‌طور
# منظم"): at least one Report Employee Run in the trailing window.
# Deliberately simple and explicit rather than a hidden constant buried in
# a query, so the product team can tune it without spelunking.
ACTIVE_WINDOW_DAYS = 14
PHASE3_CUSTOMER_TARGET = 3


async def create_feedback(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    rating: int,
    comment: str | None,
    run_id: uuid.UUID | None,
    employee_id: uuid.UUID | None,
    category: str,
) -> Feedback:
    if run_id is not None:
        run = (
            await db.execute(
                select(Run).where(Run.id == run_id, Run.tenant_id == tenant_id)
            )
        ).scalar_one_or_none()
        if run is None:
            raise NotFoundError("Run not found")
        if employee_id is None:
            employee_id = run.employee_id

    if employee_id is not None:
        employee = (
            await db.execute(select(Employee).where(Employee.id == employee_id))
        ).scalar_one_or_none()
        if employee is None or (employee.tenant_id is not None and employee.tenant_id != tenant_id):
            raise ValidationAppError("employee_id does not reference an employee available to this tenant")

    feedback = Feedback(
        tenant_id=tenant_id,
        user_id=user_id,
        run_id=run_id,
        employee_id=employee_id,
        rating=rating,
        comment=comment,
        category=category,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


async def list_feedback(db: AsyncSession, *, tenant_id: uuid.UUID | None, limit: int = 50) -> list[Feedback]:
    stmt = select(Feedback).order_by(Feedback.created_at.desc()).limit(limit)
    if tenant_id is not None:
        stmt = stmt.where(Feedback.tenant_id == tenant_id)
    return list((await db.execute(stmt)).scalars().all())


async def validation_summary(db: AsyncSession) -> dict:
    """Platform-admin aggregate view mapping directly onto the Roadmap's
    Phase 3 Definition of Done. Restricted to the `report-employee` system
    Employee's Runs, since that is explicitly the Phase 2/3 product."""
    report_employee = (
        await db.execute(
            select(Employee).where(Employee.tenant_id.is_(None), Employee.slug == "report-employee")
        )
    ).scalar_one_or_none()

    cutoff = datetime.now(timezone.utc) - timedelta(days=ACTIVE_WINDOW_DAYS)

    tenants = list((await db.execute(select(Tenant))).scalars().all())

    tenant_rows = []
    active_tenant_count = 0
    for tenant in tenants:
        runs_total = 0
        runs_recent = 0
        last_run_at = None
        if report_employee is not None:
            runs_total = (
                await db.execute(
                    select(func.count())
                    .select_from(Run)
                    .where(Run.tenant_id == tenant.id, Run.employee_id == report_employee.id)
                )
            ).scalar_one()
            runs_recent = (
                await db.execute(
                    select(func.count())
                    .select_from(Run)
                    .where(
                        Run.tenant_id == tenant.id,
                        Run.employee_id == report_employee.id,
                        Run.created_at >= cutoff,
                    )
                )
            ).scalar_one()
            last_run_at = (
                await db.execute(
                    select(func.max(Run.created_at)).where(
                        Run.tenant_id == tenant.id, Run.employee_id == report_employee.id
                    )
                )
            ).scalar_one()

        feedback_count = (
            await db.execute(
                select(func.count()).select_from(Feedback).where(Feedback.tenant_id == tenant.id)
            )
        ).scalar_one()
        avg_rating = (
            await db.execute(
                select(func.avg(Feedback.rating)).where(Feedback.tenant_id == tenant.id)
            )
        ).scalar_one()

        if runs_recent > 0:
            active_tenant_count += 1

        tenant_rows.append(
            {
                "tenant_id": tenant.id,
                "tenant_name": tenant.name,
                "report_employee_runs_last_14d": runs_recent,
                "report_employee_runs_total": runs_total,
                "last_run_at": last_run_at,
                "feedback_count": feedback_count,
                "avg_rating": float(avg_rating) if avg_rating is not None else None,
            }
        )

    total_feedback_count = (
        await db.execute(select(func.count()).select_from(Feedback))
    ).scalar_one()
    overall_avg_rating = (await db.execute(select(func.avg(Feedback.rating)))).scalar_one()

    recent_feedback = list(
        (
            await db.execute(select(Feedback).order_by(Feedback.created_at.desc()).limit(20))
        )
        .scalars()
        .all()
    )

    return {
        "active_tenant_count": active_tenant_count,
        "meets_phase3_customer_criteria": active_tenant_count >= PHASE3_CUSTOMER_TARGET,
        "phase3_customer_target": PHASE3_CUSTOMER_TARGET,
        "total_feedback_count": total_feedback_count,
        "overall_avg_rating": float(overall_avg_rating) if overall_avg_rating is not None else None,
        "tenants": tenant_rows,
        "recent_feedback": recent_feedback,
    }
