from pathlib import Path

SOURCE = Path(__file__).parents[1] / "app/services/workflow_trigger_service.py"


def test_event_dispatch_locks_delivery_before_creating_workflow_run():
    source = SOURCE.read_text()
    assert 'select(WorkflowEventDelivery).where(WorkflowEventDelivery.id == delivery_id).with_for_update()' in source
    assert 'select(WorkflowEventDelivery).where(WorkflowEventDelivery.id == delivery_id))' not in source
