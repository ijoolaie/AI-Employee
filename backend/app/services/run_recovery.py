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

    The Run row is locked before the recovery transition so duplicate Celery
    redeliveries cannot both emit recovery transitions/audit entries.
    """
    if run.status != "running" or run.started_at is None:
        return False

    # Avoid a database round-trip for the overwhelmingly common fresh-run
    # path. The lock below remains the authority for the actual transition.
    now = datetime.now(timezone.utc)
    if now - run.started_at <= timedelta(seconds=STALE_RUN_RECOVERY_SECONDS):
        return False

    locked_result = await db.execute(
        select(Run).where(Run.id == run.id).with_for_update()
    )
    locked_run = locked_result.scalar_one_or_none()
    if (
        locked_run is None
        or locked_run.status != "running"
        or locked_run.started_at is None
    ):
        return False

    now = datetime.now(timezone.utc)
    if now - locked_run.started_at <= timedelta(
        seconds=STALE_RUN_RECOVERY_SECONDS
    ):
        return False

    logical_run_id = str(locked_run.id)
    result = await db.execute(
        select(AIProviderCall).where(
            or_(
                AIProviderCall.run_id == locked_run.id,
                AIProviderCall.raw_meta["logical_run_id"].astext == logical_run_id,
            )
        )
    )
    calls = list(result.scalars().all())

    reason = "stale_worker_execution"
    error_message = (
        "Run execution exceeded the worker recovery window. Provider outcome "
        "is ambiguous; replay was intentionally blocked."
    )

    recovered_unknown_count = 0
    for call in calls:
        if call.status == "in_flight":
            call.status = "unknown"
            call.error_message = error_message[:1000]
            call.raw_meta = {
                **(call.raw_meta or {}),
                "ambiguous_provider_outcome": True,
                "recovered_from_stale_worker": True,
                "recovery_reason": reason,
                "recovered_at": now.isoformat(),
            }
            recovered_unknown_count += 1

    # Reconcile only from provider calls that are already durably finalized as
    # successful. Unknown/in-flight outcomes are deliberately excluded.
    successful_calls = [call for call in calls if call.status == "success"]
    locked_run.total_tokens = sum(
        int(call.prompt_tokens or 0) + int(call.completion_tokens or 0)
        for call in successful_calls
    )
    locked_run.total_cost_usd = sum(
        (call.cost_usd or 0) for call in successful_calls
    )
    locked_run.status = "failed"
    locked_run.error_message = error_message[:2000]
    locked_run.completed_at = now

    await audit_service.record(
        db,
        action="run.execution_recovered",
        actor_type="system",
        tenant_id=locked_run.tenant_id,
        resource_type="run",
        resource_id=locked_run.id,
        status="failure",
        request_id=locked_run.request_id,
        metadata={
            "reason": reason,
            "provider_call_count": len(calls),
            "in_flight_call_count": recovered_unknown_count,
            "successful_call_count": len(successful_calls),
            "replay_blocked": True,
            "recovery_window_seconds": STALE_RUN_RECOVERY_SECONDS,
            "usage_reconciled_from_durable_provider_calls": True,
        },
    )
    await db.flush()
    return True
