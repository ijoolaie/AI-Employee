"""Governed workforce scaling proposal control loop."""
from __future__ import annotations

import math
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.agent_template import AgentTemplate
from app.services.agent_workforce_proposal_service import create_proposal
from app.services.capacity_forecasting import CapacityForecast, capacity_forecast

GOVERNED_SCALING_CONTRACT_VERSION = "stage9-governed-scaling-v1"
MAX_ADDITIONAL_CONCURRENCY = 4
MAX_PROJECTED_UTILIZATION_FOR_PROPOSAL = 2.0


async def create_scaling_proposal(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    requester_user_id: uuid.UUID,
    sponsor_user_id: uuid.UUID,
    agent_template_id: uuid.UUID,
    requested_name_prefix: str,
    window_days: int = 30,
    horizon_days: int = 7,
    max_additional_concurrency: int = 1,
) -> tuple[object, CapacityForecast]:
    """Turn capacity evidence into one governed workforce scaling proposal.

    The control loop never provisions, enables, assigns, or changes Agent
    capacity. It creates the existing workforce proposal, which must pass
    Board/CEO governance before provisioning and activation can occur.
    """
    if requester_user_id == sponsor_user_id:
        raise ValidationAppError("Requester and sponsor must be independently attributable")
    if not 1 <= max_additional_concurrency <= MAX_ADDITIONAL_CONCURRENCY:
        raise ValidationAppError(
            f"max_additional_concurrency must be between 1 and {MAX_ADDITIONAL_CONCURRENCY}"
        )

    template = (
        await db.execute(
            select(AgentTemplate).where(
                AgentTemplate.id == agent_template_id,
                AgentTemplate.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if template is None:
        raise NotFoundError("Agent template not found for tenant")
    if template.status.value != "published":
        raise ValidationAppError("Scaling proposal requires a published AgentTemplate")

    forecast = await capacity_forecast(
        db,
        tenant_id=tenant_id,
        window_days=window_days,
        horizon_days=horizon_days,
    )
    if not forecast.evidence_complete:
        raise ValidationAppError("Scaling proposal requires complete capacity evidence")
    if forecast.total_max_concurrency <= 0:
        raise ValidationAppError("Scaling proposal requires existing enabled Agent capacity evidence")
    if forecast.projected_utilization <= 1.0:
        raise ValidationAppError("Current capacity does not show a projected scaling need")
    if forecast.projected_utilization > MAX_PROJECTED_UTILIZATION_FOR_PROPOSAL:
        raise ValidationAppError("Projected scaling need exceeds the governed proposal safety bound")

    required_total = math.ceil(forecast.projected_required_concurrency)
    additional_concurrency = max(1, required_total - forecast.total_max_concurrency)
    requested_concurrency = min(max_additional_concurrency, additional_concurrency)

    configuration = {
        "max_concurrency": requested_concurrency,
        "budget_policy": {"max_additional_concurrency": requested_concurrency},
        "scaling_control": {
            "contract_version": GOVERNED_SCALING_CONTRACT_VERSION,
            "window_days": window_days,
            "horizon_days": horizon_days,
            "observed_capacity": forecast.total_max_concurrency,
            "projected_required_concurrency": forecast.projected_required_concurrency,
            "projected_utilization": forecast.projected_utilization,
            "projected_backlog": forecast.projected_backlog,
            "additional_concurrency_requested": requested_concurrency,
        },
    }

    proposal = await create_proposal(
        db,
        tenant_id=tenant_id,
        requester_user_id=requester_user_id,
        title="Governed workforce scaling proposal",
        rationale=(
            "Capacity evidence indicates projected demand above current enabled "
            f"concurrency ({forecast.projected_utilization:.2f}x). "
            f"Requested additional concurrency: {requested_concurrency}."
        ),
        requested_name=f"{requested_name_prefix}-{uuid.uuid4().hex[:8]}",
        sponsor_user_id=sponsor_user_id,
        agent_template_id=agent_template_id,
        risk_tier=template.risk_tier,
        configuration=configuration,
    )
    return proposal, forecast
