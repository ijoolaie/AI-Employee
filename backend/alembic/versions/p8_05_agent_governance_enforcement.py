"""Stage 8 evaluation evidence, agent identity, access reviews and Run binding.

Revision ID: p8_05_agent_governance_enforcement
Revises: p8_06_agent_instance_lifecycle
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p8_05_agent_governance_enforcement"
down_revision = "p8_06_agent_instance_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    evaluation_status = postgresql.ENUM("passed", "failed", "blocked", name="agentevaluationstatus", create_type=False)
    evaluation_status.create(op.get_bind(), checkfirst=True)
    review_decision = postgresql.ENUM("approved", "revoked", name="agentaccessreviewdecision", create_type=False)
    review_decision.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "agent_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("agent_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_templates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("suite_id", sa.String(120), nullable=False),
        sa.Column("status", evaluation_status, nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("evidence_hash", sa.String(128), nullable=True),
        sa.Column("evaluator_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_evaluations_template_created", "agent_evaluations", ["agent_template_id", "created_at"])
    op.create_index("ix_agent_evaluations_tenant_status", "agent_evaluations", ["tenant_id", "status"])

    op.create_table(
        "agent_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("agent_instance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_instances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sponsor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("agent_instance_id", name="uq_agent_identities_instance"),
    )
    op.create_index("ix_agent_identities_tenant_instance", "agent_identities", ["tenant_id", "agent_instance_id"])
    op.create_index("ix_agent_identities_expiry", "agent_identities", ["tenant_id", "expires_at"])

    op.create_table(
        "agent_access_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("agent_identity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_identities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", review_decision, nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_agent_access_reviews_tenant_identity", "agent_access_reviews", ["tenant_id", "agent_identity_id"])
    op.create_index("ix_agent_access_reviews_due", "agent_access_reviews", ["tenant_id", "next_review_at"])

    op.add_column("runs", sa.Column("agent_instance_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_runs_agent_instance", "runs", "agent_instances", ["agent_instance_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_runs_agent_instance_id", "runs", ["agent_instance_id"])


def downgrade() -> None:
    op.drop_index("ix_runs_agent_instance_id", table_name="runs")
    op.drop_constraint("fk_runs_agent_instance", "runs", type_="foreignkey")
    op.drop_column("runs", "agent_instance_id")
    op.drop_index("ix_agent_access_reviews_due", table_name="agent_access_reviews")
    op.drop_index("ix_agent_access_reviews_tenant_identity", table_name="agent_access_reviews")
    op.drop_table("agent_access_reviews")
    op.drop_index("ix_agent_identities_expiry", table_name="agent_identities")
    op.drop_index("ix_agent_identities_tenant_instance", table_name="agent_identities")
    op.drop_table("agent_identities")
    op.drop_index("ix_agent_evaluations_tenant_status", table_name="agent_evaluations")
    op.drop_index("ix_agent_evaluations_template_created", table_name="agent_evaluations")
    op.drop_table("agent_evaluations")
    postgresql.ENUM(name="agentaccessreviewdecision").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="agentevaluationstatus").drop(op.get_bind(), checkfirst=True)
