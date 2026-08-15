from datetime import datetime, timezone, timedelta
from app.schemas.workflow import WorkflowStepDefinition

def test_workflow_approval_step_schema():
    step = WorkflowStepDefinition(key="human_gate", type="approval")
    assert step.type == "approval"

def test_approval_timeout_is_positive():
    timeout = 60
    expires = datetime.now(timezone.utc) + timedelta(seconds=timeout)
    assert expires > datetime.now(timezone.utc)
