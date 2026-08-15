"""Phase 1 workflow versioning and execution-contract hardening.

Revision ID: f8d9e0a1b234
Revises: f7c8d9e0a123
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f8d9e0a1b234"
down_revision = "f7c8d9e0a123"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow_versions",
        sa.Column("execution_contract", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column("workflow_versions", sa.Column("content_hash", sa.String(length=64), nullable=True))

    # uq_workflow_version_number is created by the workflow foundation
    # migration (f1b2c3d4e506). Do not recreate it here.
    # Existing releases pre-date the explicit execution-contract snapshot. Keep
    # their immutable definitions intact and mark them as legacy; new runs can
    # materialize a deterministic contract from the legacy definition once.
    op.execute(
        """
        UPDATE workflow_versions
        SET execution_contract = jsonb_build_object(
            'schema_version', 1,
            'legacy', true,
            'workflow_version_number', version_number,
            'steps', COALESCE(config->'steps', '[]'::jsonb),
            'max_runtime_seconds', config->'max_runtime_seconds'
        )
        WHERE execution_contract = '{}'::jsonb
        """
    )

    # Keep the newest version current if historical data contains more than one
    # current marker. This makes the invariant safe before adding the partial index.
    op.execute(
        """
        UPDATE workflow_versions AS w
        SET is_current = false
        WHERE w.is_current = true
          AND w.id NOT IN (
            SELECT DISTINCT ON (workflow_id) id
            FROM workflow_versions
            WHERE is_current = true
            ORDER BY workflow_id, version_number DESC
          )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_workflow_single_current_version ON workflow_versions (workflow_id) WHERE is_current = true"
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_workflow_version_mutation()
        RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'workflow_versions are immutable; delete is forbidden';
          END IF;
          IF NEW.workflow_id IS DISTINCT FROM OLD.workflow_id
             OR NEW.version_number IS DISTINCT FROM OLD.version_number
             OR NEW.trigger_type IS DISTINCT FROM OLD.trigger_type
             OR NEW.config IS DISTINCT FROM OLD.config
             OR NEW.execution_contract IS DISTINCT FROM OLD.execution_contract
             OR NEW.content_hash IS DISTINCT FROM OLD.content_hash
             OR NEW.created_by IS DISTINCT FROM OLD.created_by
             OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
            RAISE EXCEPTION 'workflow_versions are immutable; create a new version instead';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_workflow_versions_immutable
        BEFORE UPDATE OR DELETE ON workflow_versions
        FOR EACH ROW EXECUTE FUNCTION prevent_workflow_version_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_workflow_versions_immutable ON workflow_versions")
    op.execute("DROP FUNCTION IF EXISTS prevent_workflow_version_mutation()")
    op.drop_index("uq_workflow_single_current_version", table_name="workflow_versions")
    op.drop_column("workflow_versions", "content_hash")
    op.drop_column("workflow_versions", "execution_contract")
