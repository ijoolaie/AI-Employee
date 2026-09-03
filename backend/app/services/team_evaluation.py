"""Tenant-scoped immutable TeamEvaluation service."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.test_center_safety import sanitize_test_payload
from app.models.team_definition import TeamDefinition
from app.models.team_evaluation import TeamEvaluation
from app.models.team_version import TeamVersion


class TeamEvaluationError(ValueError):
    """Raised when evaluation evidence violates the team boundary."""


class TeamEvaluationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        team_version_id: uuid.UUID,
        evaluator_id: uuid.UUID | None,
        evaluation_type: str,
        score: float | None,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        metrics: dict[str, Any],
        notes: str | None,
        evidence_class: str = "engineering",
    ) -> TeamEvaluation:
        evaluation_type = evaluation_type.strip()
        if not evaluation_type or len(evaluation_type) > 80:
            raise TeamEvaluationError("evaluation_type is required")
        if score is not None and not 0 <= score <= 1:
            raise TeamEvaluationError("score must be between 0 and 1")
        if evidence_class not in {"engineering", "external_acceptance"}:
            raise TeamEvaluationError("invalid evidence_class")
        if notes is not None and len(notes) > 4000:
            raise TeamEvaluationError("notes are too long")

        row = await self.db.execute(
            select(TeamVersion, TeamDefinition)
            .join(TeamDefinition, TeamDefinition.id == TeamVersion.team_id)
            .where(TeamVersion.id == team_version_id, TeamDefinition.tenant_id == tenant_id)
        )
        pair = row.one_or_none()
        if pair is None:
            raise TeamEvaluationError("team version not found")

        try:
            safe_input = sanitize_test_payload(input_data)
            safe_output = sanitize_test_payload(output_data)
            safe_metrics = sanitize_test_payload(metrics)
        except ValueError as exc:
            raise TeamEvaluationError(str(exc)) from exc

        evaluation = TeamEvaluation(
            tenant_id=tenant_id,
            team_version_id=team_version_id,
            evaluator_id=evaluator_id,
            evaluation_type=evaluation_type,
            score=score,
            status="recorded",
            evidence_class=evidence_class,
            input_data=safe_input,
            output_data=safe_output,
            metrics=safe_metrics,
            notes=notes,
        )
        self.db.add(evaluation)
        await self.db.flush()
        return evaluation

    async def get(self, *, tenant_id: uuid.UUID, evaluation_id: uuid.UUID) -> TeamEvaluation:
        result = await self.db.execute(
            select(TeamEvaluation).where(TeamEvaluation.id == evaluation_id, TeamEvaluation.tenant_id == tenant_id)
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise TeamEvaluationError("team evaluation not found")
        return item

    async def list(
        self,
        *,
        tenant_id: uuid.UUID,
        team_version_id: uuid.UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TeamEvaluation]:
        if not 1 <= limit <= 200 or offset < 0:
            raise TeamEvaluationError("invalid pagination")
        query = select(TeamEvaluation).where(TeamEvaluation.tenant_id == tenant_id)
        if team_version_id is not None:
            query = query.where(TeamEvaluation.team_version_id == team_version_id)
        result = await self.db.execute(query.order_by(TeamEvaluation.created_at.desc(), TeamEvaluation.id.desc()).limit(limit).offset(offset))
        return list(result.scalars().all())
