"""Phase 12.4 Test Center evidence and artifact references.

Revision ID: p12_04_test_evidence
Revises: p12_01_test_center
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p12_04_test_evidence"
down_revision = "p12_01_test_center"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("test_runs", sa.Column("runtime_version", sa.String(length=120), nullable=True))
    op.add_column("test_runs", sa.Column("migration_identity", sa.String(length=120), nullable=True))
    op.add_column("test_runs", sa.Column("git_sha", sa.String(length=64), nullable=True))
    op.add_column("test_runs", sa.Column("evidence_boundary", sa.String(length=80), nullable=False, server_default="engineering_product_evidence"))
    op.create_index("ix_test_runs_tenant_git_sha", "test_runs", ["tenant_id", "git_sha"])

    op.create_table(
        "test_run_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_type", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("reference", sa.String(length=2048), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_test_run_artifacts_tenant_run", "test_run_artifacts", ["tenant_id", "test_run_id"])
    op.create_index("ix_test_run_artifacts_tenant_type", "test_run_artifacts", ["tenant_id", "artifact_type"])


def downgrade() -> None:
    op.drop_index("ix_test_run_artifacts_tenant_type", table_name="test_run_artifacts")
    op.drop_index("ix_test_run_artifacts_tenant_run", table_name="test_run_artifacts")
    op.drop_table("test_run_artifacts")
    op.drop_index("ix_test_runs_tenant_git_sha", table_name="test_runs")
    op.drop_column("test_runs", "evidence_boundary")
    op.drop_column("test_runs", "git_sha")
    op.drop_column("test_runs", "migration_identity")
    op.drop_column("test_runs", "runtime_version")
