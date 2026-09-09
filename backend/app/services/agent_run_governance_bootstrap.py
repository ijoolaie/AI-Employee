"""Bootstrap the Agent governance context around canonical Run execution."""
from __future__ import annotations

from functools import wraps
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.services import agent_tool_governance
from app.services.agent_policy_engine import PolicyRequest, assert_authorized


_INSTALLED = False


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    # Import lazily so this module is safe when loaded from the services
    # package bootstrap itself.
    from app.services import run_service

    original_execute_run = run_service.execute_run

    @wraps(original_execute_run)
    async def governed_execute_run(db: Any, *, run_id: UUID) -> Run:
        # Production execution always uses AsyncSession. Lightweight service
        # doubles are intentionally allowed to call the canonical function
        # directly so existing unit contracts do not need to emulate a full
        # SQLAlchemy session merely to test Employee guardrails.
        if not isinstance(db, AsyncSession):
            return await original_execute_run(db, run_id=run_id)

        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run is None or run.agent_instance_id is None:
            return await original_execute_run(db, run_id=run_id)

        # Agent authorization must be re-established at the worker execution
        # boundary, not only when the WorkItem is dispatched. This closes the
        # revoke/disable/kill-switch race where a queued Run could otherwise
        # reach the AI provider after its authority changed.
        await assert_authorized(
            db,
            PolicyRequest(
                tenant_id=run.tenant_id,
                agent_instance_id=run.agent_instance_id,
                action="run.execute",
                run_id=run.id,
            ),
        )

        async with agent_tool_governance.agent_tool_context(
            tenant_id=run.tenant_id,
            agent_instance_id=run.agent_instance_id,
            run_id=run.id,
        ):
            return await original_execute_run(db, run_id=run_id)

    run_service.execute_run = governed_execute_run  # type: ignore[method-assign]
    _INSTALLED = True


install()
