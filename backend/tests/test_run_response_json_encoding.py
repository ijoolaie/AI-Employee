from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.api.v1.runs import _to_response


def test_run_response_encodes_nested_persisted_json_values():
    employee_id = uuid4()
    employee_version_id = uuid4()
    nested_uuid = uuid4()
    created_at = datetime.now(timezone.utc)

    run = SimpleNamespace(
        id=uuid4(),
        employee_id=employee_id,
        employee_version_id=employee_version_id,
        status="success",
        input_data={"request_id": nested_uuid, "amount": Decimal("12.50")},
        output_data={
            "result": {"reference_id": nested_uuid},
            "cost": Decimal("0.125000"),
            "created_at": created_at,
        },
        error=None,
        total_tokens=Decimal("42"),
        total_cost_usd=Decimal("0.125000"),
        started_at=created_at,
        completed_at=created_at,
        created_at=created_at,
    )

    response = _to_response(run, {employee_id: ("Certification Employee", "certification-employee")})
    payload = response.model_dump(mode="json")

    assert payload["input_data"]["request_id"] == str(nested_uuid)
    assert payload["input_data"]["amount"] == 12.5
    assert payload["output_data"]["result"]["reference_id"] == str(nested_uuid)
    assert payload["output_data"]["cost"] == 0.125
    assert payload["output_data"]["created_at"].endswith("+00:00")
    assert payload["total_tokens"] == 42
    assert payload["total_cost_usd"] == 0.125
