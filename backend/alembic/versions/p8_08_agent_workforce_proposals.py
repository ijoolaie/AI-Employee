"""Persist dynamic Agent workforce governance proposals.

Revision ID: p8_08_agent_workforce
Revises: p8_07_gov_merge
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p8_08_agent_workforce"
down_revision = "p8_07_gov_merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    proposal_status = postgresql.ENUM(
        "submitted", "board_approved", "board_rejected", "ceo_approved",
        "ceo_rejected", "provisioned", "cancelled",
        name="agentworkforceproposalstatus",
    )
    proposal_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "agent_workforce_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("agent_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_templates.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("agent_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_definitions.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("requested_name", sa.String(length=255), nullable=False),
        sa.Column("requester_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sponsor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("risk_tier", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("configuration", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", proposal_status, nullable=False, server_default="submitted"),
        sa.Column("board_reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("board_decision_reason", sa.Text(), nullable=True),
        sa.Column("ceo_approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("ceo_decision_reason", sa.Text(), nullable=True),
        sa.Column("provisioned_agent_instance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_instances.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_workforce_proposals_tenant_status", "agent_workforce_proposals", ["tenant_id", "status"])
    op.create_index("ix_agent_workforce_proposals_tenant_template", "agent_workforce_proposals", ["tenant_id", "agent_template_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_workforce_proposals_tenant_template", table_name="agent_workforce_proposals")
    op.drop_index("ix_agent_workforce_proposals_tenant_status", table_name="agent_workforce_proposals")
    op.drop_table("agent_workforce_proposals")
    sa.Enum(name="agentworkforceproposalstatus").drop(op.get_bind(), checkfirst=True)
