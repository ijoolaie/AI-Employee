"""W16 immutable published skill package content.

Revision ID: w16_skill_package_immutability
Revises: w16_tenant_db_invariants
"""
from alembic import op

revision = "w16_skill_package_immutability"
down_revision = "w16_tenant_db_invariants"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_published_skill_package_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF OLD.published_at IS NOT NULL AND (
                NEW.id IS DISTINCT FROM OLD.id OR
                NEW.tenant_id IS DISTINCT FROM OLD.tenant_id OR
                NEW.product_id IS DISTINCT FROM OLD.product_id OR
                NEW.slug IS DISTINCT FROM OLD.slug OR
                NEW.name IS DISTINCT FROM OLD.name OR
                NEW.description IS DISTINCT FROM OLD.description OR
                NEW.version IS DISTINCT FROM OLD.version OR
                NEW.manifest IS DISTINCT FROM OLD.manifest OR
                NEW.compatibility IS DISTINCT FROM OLD.compatibility OR
                NEW.presentation_metadata IS DISTINCT FROM OLD.presentation_metadata OR
                NEW.published_at IS DISTINCT FROM OLD.published_at
            ) THEN
                RAISE EXCEPTION
                    'published skill package content is immutable'
                    USING ERRCODE = 'check_violation';
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_skill_packages_published_immutable
        BEFORE UPDATE ON skill_packages
        FOR EACH ROW
        EXECUTE FUNCTION prevent_published_skill_package_mutation();
        """
    )


def downgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS trg_skill_packages_published_immutable ON skill_packages;"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS prevent_published_skill_package_mutation();"
    )
