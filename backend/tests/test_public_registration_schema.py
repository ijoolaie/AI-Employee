import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest


def _payload(**overrides):
    values = {
        "tenant_name": "Example account",
        "tenant_slug": "example-account",
        "email": "owner@example.com",
        "password": "Strong-Test-Password-2026!",
    }
    values.update(overrides)
    return values


def test_public_registration_defaults_to_customer():
    payload = RegisterRequest.model_validate(_payload())
    assert payload.tenant_kind == "customer"


def test_public_registration_accepts_reseller():
    payload = RegisterRequest.model_validate(_payload(tenant_kind="reseller"))
    assert payload.tenant_kind == "reseller"


def test_public_registration_cannot_create_vendor():
    with pytest.raises(ValidationError):
        RegisterRequest.model_validate(_payload(tenant_kind="vendor"))