"""Phase 5 commercial license authority.

Revision ID: p5license01
Revises: rc9merge02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p5license01"
down_revision = "rc9merge02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commercial_licenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("license_key", sa.String(80), nullable=False),
        sa.Column("issuer_tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("edition", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revocation_reason", sa.Text()),
        sa.Column("feature_codes", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("license_key", name="uq_commercial_license_key"),
    )
    op.create_index("ix_commercial_licenses_license_key", "commercial_licenses", ["license_key"], unique=True)
    op.create_index("ix_commercial_license_tenant_status", "commercial_licenses", ["tenant_id", "status"])
    op.create_index("ix_commercial_license_issuer", "commercial_licenses", ["issuer_tenant_id"])

    # Existing deployments are grandfathered with explicit, perpetual licenses so
    # enabling the execution gate does not unexpectedly disable existing tenants.
    op.execute(sa.text("""
        INSERT INTO commercial_licenses
            (id, license_key, issuer_tenant_id, tenant_id, edition, status, feature_codes, metadata)
        SELECT
            gen_random_uuid(),
            'LEGACY-' || replace(t.id::text, '-', ''),
            COALESCE(t.parent_tenant_id, t.id),
            t.id,
            t.tenant_kind,
            'active',
            '[]'::jsonb,
            '{\"source\": \"phase5-migration\", \"grandfathered\": true}'::jsonb
        FROM tenants t
        WHERE NOT EXISTS (
            SELECT 1 FROM commercial_licenses cl WHERE cl.tenant_id = t.id AND cl.status = 'active'
        )
    """))


def downgrade() -> None:
    op.drop_index("ix_commercial_license_issuer", table_name="commercial_licenses")
    op.drop_index("ix_commercial_license_tenant_status", table_name="commercial_licenses")
    op.drop_index("ix_commercial_licenses_license_key", table_name="commercial_licenses")
    op.drop_table("commercial_licenses")
