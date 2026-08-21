from app.models.outbox import OutboxMessage
from app.models.workflow import WorkflowParallelBranchRun, WorkflowRun, WorkflowStepRun
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowParallelBranch,
    WorkflowRunCreate,
    WorkflowStepDefinition,
)


def test_parallel_workflow_schema():
    payload = WorkflowCreate(
        slug="parallel-flow",
        name="Parallel Flow",
        steps=[
            WorkflowStepDefinition(
                key="parallel",
                type="parallel",
                branches=[
                    WorkflowParallelBranch(
                        key="a",
                        steps=[
                            {
                                "key": "a1",
                                "type": "employee",
                                "employee_id": "8740db8a-87b5-4f68-aa52-b270d96e0555",
                            }
                        ],
                    ),
                    WorkflowParallelBranch(
                        key="b",
                        steps=[
                            {
                                "key": "b1",
                                "type": "employee",
                                "employee_id": "8740db8a-87b5-4f68-aa52-b270d96e0555",
                            }
                        ],
                    ),
                ],
            )
        ],
    )
    assert payload.steps[0].type == "parallel"
    assert len(payload.steps[0].branches) == 2


def test_idempotency_and_retry_fields_exist():
    assert hasattr(WorkflowRun, "idempotency_key")
    assert hasattr(WorkflowStepRun, "next_retry_at")
    assert hasattr(WorkflowStepRun, "last_error")
    assert hasattr(OutboxMessage, "dedupe_key")
    assert hasattr(WorkflowParallelBranchRun, "branch_key")


def test_run_payload_accepts_idempotency_key():
    payload = WorkflowRunCreate(input_data={"x": 1}, idempotency_key="client-request-001")
    assert payload.idempotency_key == "client-request-001"
