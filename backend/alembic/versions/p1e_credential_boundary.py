"""P1-E encrypted credential boundary.

New credentials are stored encrypted and referenced by opaque IDs. Existing
legacy plaintext integration config is intentionally not auto-converted here;
operators must rotate those credentials through the new vault before enabling
agent access, avoiding a migration that depends on runtime secret material.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p1ecredentialboundary"
down_revision = "p1dagentkillswitch"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_credentials_tenant_status", "credentials", ["tenant_id", "status"])
    op.create_index("ix_credentials_tenant_provider", "credentials", ["tenant_id", "provider"])
    op.execute(sa.text("""
        INSERT INTO permissions (id, code, description)
        VALUES (gen_random_uuid(), 'credential.read', 'Resolve encrypted provider credentials at governed side-effect boundaries')
        ON CONFLICT (code) DO NOTHING
    """))


def downgrade() -> None:
    op.drop_index("ix_credentials_tenant_provider", table_name="credentials")
    op.drop_index("ix_credentials_tenant_status", table_name="credentials")
    op.drop_table("credentials")
