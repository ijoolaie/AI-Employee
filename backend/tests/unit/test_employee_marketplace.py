from app.services.employee_marketplace_service import _validate_untrusted_manifest


def test_employee_marketplace_rejects_execution_authority_metadata():
    for key in ("grants_execution", "auto_activate", "bypass_approval", "provider_credentials"):
        try:
            _validate_untrusted_manifest({key: True}, "manifest")
        except Exception as exc:
            assert "forbidden execution authority" in str(exc)
        else:
            raise AssertionError(f"{key} was accepted")


def test_employee_marketplace_accepts_presentation_metadata():
    _validate_untrusted_manifest({"theme": "technical", "avatar_ref": "fixture"}, "visual_pack")
