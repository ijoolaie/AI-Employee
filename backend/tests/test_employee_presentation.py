from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.employee import EmployeePresentationProfile
from app.services import employee_service


# W14 presentation customization remains presentation-only; execution authority is unchanged.
def test_presentation_profile_defaults_are_bounded():
    profile = EmployeePresentationProfile()
    assert profile.model_dump() == {
        "gender_presentation": "neutral",
        "outfit": "business",
        "hair_style": "default",
        "accessory": "none",
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("gender_presentation", "admin"),
        ("outfit", "production"),
        ("hair_style", "arbitrary"),
        ("accessory", "execute"),
    ],
)
def test_presentation_profile_rejects_unsupported_values(field, value):
    with pytest.raises(ValidationError):
        EmployeePresentationProfile(**{field: value})


@pytest.mark.asyncio
async def test_update_presentation_is_tenant_scoped_and_presentation_only(monkeypatch):
    tenant_id = uuid4()
    employee = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        presentation_profile={},
    )
    audit = []

    async def fake_get_employee(db, *, employee_id, tenant_id):
        assert tenant_id is not None
        return employee

    async def fake_record(db, **kwargs):
        audit.append(kwargs)

    class DB:
        async def flush(self):
            pass

        async def refresh(self, obj):
            pass

    monkeypatch.setattr(employee_service, "get_employee", fake_get_employee)
    monkeypatch.setattr(employee_service.audit_service, "record", fake_record)

    profile = {
        "gender_presentation": "feminine",
        "outfit": "formal",
        "hair_style": "long",
        "accessory": "glasses",
    }
    result = await employee_service.update_presentation_profile(
        DB(),
        employee_id=employee.id,
        tenant_id=tenant_id,
        presentation_profile=profile,
        actor_id=None,
    )

    assert result.presentation_profile == profile
    assert audit[0]["action"] == "employee.presentation_updated"
    assert audit[0]["metadata"]["presentation_only"] is True
