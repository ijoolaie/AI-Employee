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

class _InstallResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _InstallDB:
    def __init__(self, package):
        self.results = iter([package, None])

    async def execute(self, _statement):
        return _InstallResult(next(self.results))

    def add(self, _row):
        raise AssertionError("untrusted legacy snapshot must be rejected before writes")

    async def flush(self):
        raise AssertionError("untrusted legacy snapshot must be rejected before writes")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("template_snapshot", "definition_snapshot", "permission_manifest", "message"),
    [
        (
            {"install_policy": {"nested": [{"bypass_approval": True}]}},
            {"name": "legacy definition"},
            {},
            "forbidden execution authority",
        ),
        (
            {"install_policy": {}},
            {"model_policy": {"provider": {"api_key": "legacy-secret"}}},
            {},
            "prohibited secret field",
        ),
        (
            {"install_policy": {}},
            {"model_policy": {}},
            {"approval_policy": {"credentials": {"token": "legacy-secret"}}},
            "prohibited secret field",
        ),
    ],
)
async def test_employee_marketplace_revalidates_legacy_snapshot_before_install(
    monkeypatch, template_snapshot, definition_snapshot, permission_manifest, message
):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    from uuid import uuid4

    from app.models.employee_marketplace import EmployeeMarketplacePackageStatus
    from app.services import employee_marketplace_service

    buyer_tenant_id = uuid4()
    package = SimpleNamespace(
        id=uuid4(),
        owner_tenant_id=uuid4(),
        visibility="public",
        status=EmployeeMarketplacePackageStatus.PUBLISHED,
        employee_manifest={
            "template_snapshot": {"name": "legacy template", **template_snapshot},
            "definition_snapshot": {"name": "legacy definition", **definition_snapshot},
        },
        permission_manifest=permission_manifest,
    )
    monkeypatch.setattr(
        employee_marketplace_service,
        "assert_users_belong_to_tenant",
        AsyncMock(),
    )

    with pytest.raises(ValidationAppError, match=message):
        await employee_marketplace_service.install_package(
            _InstallDB(package),
            buyer_tenant_id=buyer_tenant_id,
            package_id=package.id,
            sponsor_user_id=uuid4(),
            actor_id=uuid4(),
        )
