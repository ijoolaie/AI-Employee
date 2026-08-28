from uuid import uuid4

from app.services.execution_telemetry import ExecutionEvent, ExecutionTelemetry


def test_telemetry_preserves_execution_correlation():
    telemetry = ExecutionTelemetry()
    tenant_id, work_item_id = uuid4(), uuid4()

    event = telemetry.emit(
        ExecutionEvent(
            tenant_id=tenant_id,
            work_item_id=work_item_id,
            event="completed",
            duration_ms=12.5,
            cost=0.03,
            tokens=42,
            correlation_id="corr-1",
        )
    )

    assert event.tenant_id == tenant_id
    assert event.work_item_id == work_item_id
    assert event.correlation_id == "corr-1"
    assert event.cost == 0.03


def test_telemetry_strips_secret_like_metadata():
    telemetry = ExecutionTelemetry()
    event = telemetry.emit(
        ExecutionEvent(
            tenant_id=uuid4(),
            work_item_id=uuid4(),
            event="started",
            metadata={"region": "eu", "api_secret": "hidden", "password": "hidden"},
        )
    )

    assert event.metadata == {"region": "eu"}
