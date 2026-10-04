from app.models.skill_marketplace_publication import SkillMarketplacePublication
from app.services.skill_marketplace_publication_service import SkillMarketplacePublicationService
from app.schemas.skill_marketplace_publication import SkillMarketplacePublicationResponse


def test_skill_marketplace_publication_requires_composite_source_tenant_fk():
    constraints = {
        tuple(column.name for column in fk.columns)
        for fk in SkillMarketplacePublication.__table__.foreign_key_constraints
    }
    assert ("owner_tenant_id", "skill_package_id") in constraints


def test_skill_marketplace_publication_has_owner_tenant_fk():
    constraints = {
        tuple(column.name for column in fk.columns)
        for fk in SkillMarketplacePublication.__table__.foreign_key_constraints
    }
    assert ("owner_tenant_id",) in constraints


def test_skill_marketplace_publication_is_unique_per_skill_package():
    unique_sets = {
        frozenset(constraint.columns.keys())
        for constraint in SkillMarketplacePublication.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert frozenset({"skill_package_id"}) in unique_sets


def test_skill_marketplace_publication_is_immutable():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "models"
        / "skill_marketplace_publication.py"
    ).read_text(encoding="utf-8")
    assert "before_update" in source
    assert "skill marketplace publication records are immutable" in source


def test_skill_marketplace_publication_has_no_execution_authority_fields():
    assert not hasattr(SkillMarketplacePublication, "allowed_tools")
    assert not hasattr(SkillMarketplacePublication, "permissions")
    assert not hasattr(SkillMarketplacePublication, "approval_policy")
    assert not hasattr(SkillMarketplacePublication, "capability_contract")
    assert not hasattr(SkillMarketplacePublication, "tool_bindings")


def test_skill_marketplace_publication_service_visibility_contract():
    assert SkillMarketplacePublicationService.VISIBILITIES == {
        "private",
        "unlisted",
        "public",
    }


def test_skill_marketplace_response_makes_boundaries_explicit():
    fields = SkillMarketplacePublicationResponse.model_fields
    assert fields["installation"].default == "not_implied"
    assert fields["execution_authority"].default == "not_implied"
    assert fields["customer_acceptance"].default == "not_implied"
    assert fields["trust_basis"].default == "recorded_evidence_only"
