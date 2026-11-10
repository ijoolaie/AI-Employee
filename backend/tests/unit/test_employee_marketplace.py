import pytest

from app.core.exceptions import ValidationAppError
from app.services.employee_marketplace_service import _validate_untrusted_manifest


def test_employee_marketplace_rejects_execution_authority_metadata():
    for key in ("grants_execution", "auto_activate", "bypass_approval", "provider_credentials"):
        with pytest.raises(ValidationAppError, match="forbidden execution authority"):
            _validate_untrusted_manifest({key: True}, "manifest")


def test_employee_marketplace_accepts_presentation_metadata():
    _validate_untrusted_manifest({"theme": "technical", "avatar_ref": "fixture"}, "visual_pack")


def test_employee_marketplace_rejects_nested_secret_fields():
    with pytest.raises(ValidationAppError, match="prohibited secret field"):
        _validate_untrusted_manifest(
            {"provider": {"settings": [{"access-token": "sensitive"}]}},
            "definition.model_policy",
        )


def test_employee_marketplace_rejects_nested_execution_authority():
    with pytest.raises(ValidationAppError, match="forbidden execution authority"):
        _validate_untrusted_manifest(
            {"workflow": [{"bypass_approval": True}]},
            "template.install_policy",
        )
