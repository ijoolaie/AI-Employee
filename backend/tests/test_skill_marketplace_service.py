from app.models.skill_package import EmployeeSkillInstallation, SkillPackage
from app.core.exceptions import ValidationAppError
from app.services.skill_marketplace_service import SkillMarketplaceError, _validate_manifest, create_package


def test_skill_manifest_cannot_declare_execution_authority():
    for key in ("allowed_tools", "permissions", "approval_policy", "capability_contract", "tool_bindings"):
        try:
            _validate_manifest({key: []})
        except SkillMarketplaceError:
            pass
        else:
            raise AssertionError(key)


def test_skill_installation_has_no_execution_authority_fields():
    assert not hasattr(EmployeeSkillInstallation, "permission_policy")
    assert not hasattr(EmployeeSkillInstallation, "allowed_tools")
    assert not hasattr(EmployeeSkillInstallation, "capability_contract")


def test_skill_package_has_no_permission_or_tool_binding_fields():
    assert not hasattr(SkillPackage, "permission_policy")
    assert not hasattr(SkillPackage, "allowed_tools")
    assert not hasattr(SkillPackage, "capability_contract")


def test_skill_marketplace_error_is_a_client_error():
    error = SkillMarketplaceError("invalid skill contract")
    assert error.code == "SKILL_MARKETPLACE_INVALID"
    assert error.status_code == 422


def test_skill_package_product_fk_is_not_nullable_on_delete():
    # The SQLAlchemy model must preserve the commercial product link.
    assert SkillPackage.__table__.c.product_id.foreign_keys
    fk = next(iter(SkillPackage.__table__.c.product_id.foreign_keys))
    assert fk.ondelete == "RESTRICT"


def test_skill_metadata_rejects_nested_execution_authority():
    nested = {"ui": {"presentation": {"permissions": ["run.execute"]}}}
    try:
        _validate_manifest(nested)
    except SkillMarketplaceError:
        pass
    else:
        raise AssertionError("nested permissions must be rejected")


def test_skill_metadata_must_be_objects():
    from app.services.skill_marketplace_service import _validate_skill_metadata

    for value in ([], "invalid", 1):
        try:
            _validate_skill_metadata(value, "skill compatibility")
        except ValidationAppError:
            pass
        else:
            raise AssertionError(value)


async def test_create_package_rejects_non_object_skill_metadata_before_db():
    import uuid

    for field in ("manifest", "compatibility", "presentation_metadata"):
        kwargs = {field: []}
        try:
            await create_package(object(), tenant_id=uuid.uuid4(), slug="bad-metadata", name="Bad Metadata", **kwargs)
        except ValidationAppError:
            pass
        else:
            raise AssertionError(field)


def test_w16_models_enforce_tenant_consistent_foreign_keys():
    installation_fks = {
        tuple(column.name for column in fk.columns)
        for fk in EmployeeSkillInstallation.__table__.foreign_key_constraints
    }
    assert ("tenant_id", "employee_id") in installation_fks
    assert ("tenant_id", "skill_package_id") in installation_fks

    package_fks = {
        tuple(column.name for column in fk.columns)
        for fk in SkillPackage.__table__.foreign_key_constraints
    }
    assert ("tenant_id", "product_id") in package_fks


def test_w16_referenced_entities_expose_composite_tenant_keys():
    from app.models.employee import Employee
    from app.models.product import Product

    assert {"tenant_id", "id"} in {
        frozenset(constraint.columns.keys())
        for constraint in Employee.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert {"tenant_id", "id"} in {
        frozenset(constraint.columns.keys())
        for constraint in Product.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert {"tenant_id", "id"} in {
        frozenset(constraint.columns.keys())
        for constraint in SkillPackage.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
