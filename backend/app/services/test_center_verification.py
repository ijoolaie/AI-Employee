"""Exportable Test Center verification records for P12.6."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_definition import TestDefinition
from app.models.test_run import TestRun, TestRunStatus
from app.models.test_run_artifact import TestRunArtifact


class VerificationRecordError(RuntimeError):
    """Raised when a verification record cannot be exported safely."""


class TestCenterVerificationService:
    """Build immutable, tenant-bound verification snapshots without mutating runs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_record(self, *, tenant_id: UUID, run_id: UUID) -> dict[str, Any]:
        run = (
            await self.db.execute(
                select(TestRun).where(TestRun.id == run_id, TestRun.tenant_id == tenant_id)
            )
        ).scalar_one_or_none()
        if run is None:
            raise VerificationRecordError("test run not found")
        if run.status not in {TestRunStatus.PASSED, TestRunStatus.FAILED}:
            raise VerificationRecordError("verification record requires a completed test run")

        definition = (
            await self.db.execute(
                select(TestDefinition).where(
                    TestDefinition.id == run.test_definition_id,
                    TestDefinition.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if definition is None:
            raise VerificationRecordError("test definition not found")

        artifacts_result = await self.db.execute(
            select(TestRunArtifact)
            .where(
                TestRunArtifact.test_run_id == run.id,
                TestRunArtifact.tenant_id == tenant_id,
            )
            .order_by(TestRunArtifact.created_at.asc(), TestRunArtifact.id.asc())
        )
        artifacts = list(artifacts_result.scalars().all())

        return {
            "record_type": "test_center_verification_record",
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc),
            "acceptance_boundary": "engineering_product_evidence",
            "acceptance_statement": (
                "This record is engineering/product evidence only and does not "
                "constitute Vendor, Reseller, Customer, or external production acceptance."
            ),
            "tenant_id": tenant_id,
            "run": {
                "id": run.id,
                "test_definition_id": run.test_definition_id,
                "workspace_key": run.workspace_key,
                "status": run.status.value,
                "actor_id": run.actor_id,
                "executor_type": run.executor_type,
                "correlation_id": run.correlation_id,
                "queued_at": run.queued_at,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "created_at": run.created_at,
                "result": run.result or {},
                "error": run.error,
                "evidence": run.evidence or {},
                "runtime_version": run.runtime_version,
                "migration_identity": run.migration_identity,
                "git_sha": run.git_sha,
                "evidence_boundary": run.evidence_boundary,
            },
            "test_definition": {
                "id": definition.id,
                "code": definition.code,
                "name": definition.name,
                "test_type": definition.test_type,
                "category": definition.category,
                "description": definition.description,
                "workspace_key": definition.workspace_key,
                "prerequisites": definition.prerequisites or {},
                "expected_result": definition.expected_result or {},
                "evidence_requirements": definition.evidence_requirements or {},
                "enabled": definition.enabled,
                "created_at": definition.created_at,
                "updated_at": definition.updated_at,
            },
            "artifacts": [
                {
                    "id": artifact.id,
                    "artifact_type": artifact.artifact_type,
                    "label": artifact.label,
                    "reference": artifact.reference,
                    "sha256": artifact.sha256,
                    "size_bytes": artifact.size_bytes,
                    "metadata": artifact.metadata or {},
                    "created_at": artifact.created_at,
                }
                for artifact in artifacts
            ],
        }
