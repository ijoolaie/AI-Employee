"""Focused governance tests for W16 payout execution."""
from pathlib import Path
import uuid

import pytest

from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError


def test_marketplace_payout_execution_tool_is_explicitly_side_effecting_and_approval_gated():
    tool = registry.get("marketplace_execute_payout")
    assert tool.side_effects is True
    assert tool.external_side_effects is True
    assert tool.required_permission == "run.execute"
    assert tool.requires_approval is True
    assert tool.input_schema["required"] == ["proposal_id"]


@pytest.mark.asyncio
async def test_marketplace_payout_execution_rejects_without_approval():
    with pytest.raises(ValidationAppError, match="Human approval required"):
        await registry.execute(
            "marketplace_execute_payout",
            {"proposal_id": str(uuid.uuid4())},
            permissions={"run.execute"},
        )


@pytest.mark.asyncio
async def test_marketplace_payout_execution_rejects_approved_flag_without_transaction_context():
    with pytest.raises(ValidationAppError, match="active Agent Run context"):
        await registry.execute(
            "marketplace_execute_payout",
            {"proposal_id": str(uuid.uuid4())},
            permissions={"run.execute"},
            approval_granted=True,
            approval_request_id=uuid.uuid4(),
        )


def test_payout_service_requires_durable_consumed_approval_and_no_generic_transport():
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "skill_marketplace_payout_service.py"
    ).read_text(encoding="utf-8")

    assert "ToolApprovalRequest" in source
    assert 'approval.status not in {"approved", "consumed"}' in source
    assert "approval.decided_by is None" in source
    assert 'approval.arguments != {"proposal_id": str(proposal_id)}' in source
    assert "get_marketplace_payout_provider()" in source
    assert "httpx" not in source
    assert "stripe" not in source.lower()


def test_payout_execution_keeps_unknown_manual_reconciliation_and_no_automatic_retry():
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "skill_marketplace_payout_service.py"
    ).read_text(encoding="utf-8")

    assert 'SkillMarketplacePayoutExecutionStatus.UNKNOWN' in source
    assert '"reconciliation_required": True' in source
    assert 'proposal.execution_status is SkillMarketplacePayoutExecutionStatus.UNKNOWN' in source
    assert "retryable = False" in source


def test_marketplace_payout_reconciliation_tool_is_distinct_approval_gated_and_non_transporting():
    tool = registry.get("marketplace_reconcile_payout")
    assert tool.side_effects is True
    assert tool.external_side_effects is False
    assert tool.required_permission == "run.execute"
    assert tool.requires_approval is True
    assert tool.input_schema["required"] == ["proposal_id", "outcome", "evidence_ref"]


def test_payout_reconciliation_requires_unknown_state_and_explicit_evidence():
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "skill_marketplace_payout_service.py"
    ).read_text(encoding="utf-8")

    assert "reconcile_unknown_payout_execution" in source
    assert 'proposal.execution_status is not SkillMarketplacePayoutExecutionStatus.UNKNOWN' in source
    assert "payout reconciliation requires an evidence reference" in source
    assert 'approval.tool_name != "marketplace_reconcile_payout"' in source
    assert 'approval.arguments != expected_arguments' in source
    assert 'action="skill_marketplace_payout.reconciled"' in source
    assert "get_marketplace_payout_provider()" not in source.split("async def reconcile_unknown_payout_execution", 1)[1].split("async def execute_payout_proposal", 1)[0]


def test_payout_reconciliation_never_claims_external_execution():
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "skill_marketplace_payout_service.py"
    ).read_text(encoding="utf-8")
    section = source.split("async def reconcile_unknown_payout_execution", 1)[1].split("async def execute_payout_proposal", 1)[0]
    assert '"external_execution": proposal.external_execution' in section
    assert "provider.create_payout" not in section
