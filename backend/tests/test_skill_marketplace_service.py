from app.models.skill_package import EmployeeSkillInstallation, SkillPackage
from app.services.skill_marketplace_service import SkillMarketplaceError, _validate_manifest


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
