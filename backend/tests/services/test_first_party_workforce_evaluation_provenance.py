from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.exceptions import ValidationAppError
from app.models.agent_evaluation import AgentEvaluationStatus
from app.models.agent_template import AgentTemplateStatus
from app.services.agent_governance import record_evaluation


@pytest.mark.asyncio
async def test_first_party_workforce_template_rejects_caller_asserted_pass_evidence():
    template = SimpleNamespace(
        id="template-id",
        status=AgentTemplateStatus.DRAFT,
        is_system_template=True,
        capability_contract={"workforce_role_code": "ai_software_developer"},
        evaluation_policy={"requires_evidence": True},
    )
    db = SimpleNamespace(execute=AsyncMock(), add=Mock())
    db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: template)

    with pytest.raises(ValidationAppError, match="trusted Test Center evaluation provenance"):
        await record_evaluation(
            db,
            tenant_id="tenant-id",
            template_id="template-id",
            suite_id="developer-workspace-v1",
            status=AgentEvaluationStatus.PASSED,
            evidence={"contract_version": "v1", "result": "passed"},
            score=100,
            evaluator_user_id=None,
            notes=None,
        )

    db.add.assert_not_called()
