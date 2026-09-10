"""Regression coverage for NULL-safe TeamInstallation uniqueness definitions."""

from pathlib import Path

from app.models.team_installation import TeamInstallation


MIGRATION = Path(__file__).parents[1] / "alembic" / "versions" / "p1g_team_installation_null_safe_scope.py"


def test_team_installation_has_explicit_partial_unique_indexes_for_nullable_scopes():
    indexes = {index.name: index for index in TeamInstallation.__table__.indexes}

    assert "uq_team_installations_tenant_version_workspace_null" in indexes
    assert "uq_team_installations_tenant_version_workspace" in indexes
    assert "uq_team_installations_tenant_publication_workspace_null" in indexes
    assert "uq_team_installations_tenant_publication_workspace" in indexes

    assert str(indexes["uq_team_installations_tenant_version_workspace_null"].dialect_options["postgresql"]["where"]) == "workspace_key IS NULL"
    assert str(indexes["uq_team_installations_tenant_version_workspace"].dialect_options["postgresql"]["where"]) == "workspace_key IS NOT NULL"


def test_migration_replaces_nullable_unique_constraints_with_partial_indexes():
    source = MIGRATION.read_text(encoding="utf-8")

    assert 'op.drop_constraint(\n        "uq_team_installations_tenant_version_workspace"' in source
    assert 'op.drop_constraint(\n        "uq_team_installations_tenant_publication_workspace"' in source
    assert '"workspace_key IS NULL"' in source
    assert '"workspace_key IS NOT NULL"' in source
    assert '"source_publication_id IS NOT NULL AND workspace_key IS NULL"' in source
    assert '"source_publication_id IS NOT NULL AND workspace_key IS NOT NULL"' in source
