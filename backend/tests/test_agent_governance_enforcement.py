from datetime import datetime, timezone

from app.models.agent_access_review import AgentAccessReview, AgentAccessReviewDecision
from app.models.agent_evaluation import AgentEvaluation, AgentEvaluationStatus
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.services.agent_governance import _hash_evidence


def test_evaluation_contract_is_persisted_as_evidence() -> None:
    columns = AgentEvaluation.__table__.c
    assert {"agent_template_id", "suite_id", "status", "score", "evidence", "evidence_hash", "evaluator_user_id"} <= set(columns.keys())
    assert {item.value for item in AgentEvaluationStatus} == {"passed", "failed", "blocked"}


def test_identity_contract_is_first_class_and_revocable() -> None:
    columns = AgentIdentity.__table__.c
    assert {"agent_instance_id", "owner_user_id", "sponsor_user_id", "subject", "expires_at", "revoked_at", "active"} <= set(columns.keys())


def test_access_review_has_independent_decisions() -> None:
    columns = AgentAccessReview.__table__.c
    assert {"agent_identity_id", "reviewer_user_id", "decision", "reviewed_at", "next_review_at"} <= set(columns.keys())
    assert {item.value for item in AgentAccessReviewDecision} == {"approved", "revoked"}


def test_evidence_hash_is_canonical_and_stable() -> None:
    first = _hash_evidence({"score": 95, "checks": ["rbac", "tenant-isolation"]})
    second = _hash_evidence({"checks": ["rbac", "tenant-isolation"], "score": 95})
    assert first == second
    assert len(first) == 64


def test_retired_instance_is_not_an_executable_state() -> None:
    assert AgentInstanceStatus.RETIRED.value == "retired"
    assert AgentInstanceStatus.ENABLED.value == "enabled"
