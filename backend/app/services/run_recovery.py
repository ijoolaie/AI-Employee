"""Safe recovery for Runs abandoned by a lost worker.

A worker can die after an external AI provider has accepted a request but
before the provider result is durably finalized. Such a call is ambiguous and
must never be replayed blindly.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_provider_call import AIProviderCall
from app.models.run import Run
from app.services import audit_service

# AgentRuntime currently bounds one execution operation to 300 seconds. Keep a
# small recovery margin so a legitimate operation is not recovered at the
# exact timeout boundary.
STALE_RUN_RECOVERY_SECONDS = 360


async def recover_stale_run_execution(db: AsyncSession, *, run: Run) -> bool:
    """Fail closed on an abandoned running Run without replaying the provider.

    Returns True when recovery was applied. The caller owns the surrounding
    transaction and must commit the recovery before returning from the worker.
    """
    if run.status != "running" or run.started_at is None:
        return False

    now = datetime.now(timezone.utc)
    if now - run.started_at <= timedelta(seconds=STALE_RUN_RECOVERY_SECONDS):
        return False

    logical_run_id = str(run.id)
    result = await db.execute(
        select(AIProviderCall).where(
            or_(
                AIProviderCall.run_id == run.id,
                AIProviderCall.raw_meta["logical_run_id"].astext == logical_run_id,
            ),
            AIProviderCall.status == "in_flight",
        )
    )
    calls = list(result.scalars().all())

    reason = "stale_worker_execution"
    error_message = (
        "Run execution exceeded the worker recovery window. Provider outcome "
        "is ambiguous; replay was intentionally blocked."
    )

    for call in calls:
        call.status = "unknown"
        call.error_message = error_message[:1000]
        call.raw_meta = {
            **(call.raw_meta or {}),
            "ambiguous_provider_outcome": True,
            "recovered_from_stale_worker": True,
            "recovery_reason": reason,
            "recovered_at": now.isoformat(),
        }

    run.status = "failed"
    run.error_message = error_message[:2000]
    run.completed_at = now

    await audit_service.record(
        db,
        action="run.execution_recovered",
        actor_type="system",
        tenant_id=run.tenant_id,
        resource_type="run",
        resource_id=run.id,
        status="failure",
        request_id=run.request_id,
        metadata={
            "reason": reason,
            "in_flight_call_count": len(calls),
            "replay_blocked": True,
            "recovery_window_seconds": STALE_RUN_RECOVERY_SECONDS,
        },
    )
    await db.flush()
    return True
