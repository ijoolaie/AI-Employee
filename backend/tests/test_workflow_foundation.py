from app.schemas.workflow import WorkflowCreate, WorkflowStepDefinition


def test_workflow_schema_accepts_linear_employee_steps():
    payload = WorkflowCreate(
        slug="support-flow",
        name="Support Flow",
        steps=[
            WorkflowStepDefinition(
                key="first",
                employee_id="8740db8a-87b5-4f68-aa52-b270d96e0555",
            )
        ],
    )
    assert payload.trigger_type == "manual"
    assert payload.steps[0].type == "employee"


def test_workflow_schema_accepts_schedule_trigger():
    payload = WorkflowCreate(slug="x", name="X", trigger_type="schedule", steps=[
        WorkflowStepDefinition(key="first", employee_id="8740db8a-87b5-4f68-aa52-b270d96e0555")
    ])
    assert payload.trigger_type == "schedule"
