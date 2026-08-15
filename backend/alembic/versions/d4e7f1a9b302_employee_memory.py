"""durable Employee memory foundation

Revision ID: d4e7f1a9b302
Revises: c1e4f8a72b31
"""
from alembic import op
import sqlalchemy as sa
import uuid
from sqlalchemy.dialects import postgresql

revision = "d4e7f1a9b302"
down_revision = "c1e4f8a72b31"
branch_labels = None
depends_on = None

def upgrade() -> None:
    permissions = sa.table("permissions", sa.column("id", postgresql.UUID(as_uuid=True)), sa.column("code", sa.String()), sa.column("description", sa.String()))
    for code, description in (("memory.read", "Read Employee memory"), ("memory.write", "Create Employee memory"), ("memory.delete", "Delete Employee memory")):
        if op.get_bind().execute(sa.text("SELECT 1 FROM permissions WHERE code = :code"), {"code": code}).first() is None:
            op.bulk_insert(permissions, [{"id": uuid.uuid4(), "code": code, "description": description}])

    op.create_table(
        "employee_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("memory_type", sa.String(length=30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["source_run_id"], ["runs.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, table, cols in (("ix_employee_memories_tenant_id", "employee_memories", ["tenant_id"]), ("ix_employee_memories_employee_id", "employee_memories", ["employee_id"]), ("ix_employee_memories_source_run_id", "employee_memories", ["source_run_id"]), ("ix_employee_memories_status", "employee_memories", ["status"]), ("ix_employee_memories_created_at", "employee_memories", ["created_at"])):
        op.create_index(name, table, cols)
    op.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r CROSS JOIN permissions p
        WHERE r.name = 'Admin' AND p.code IN ('memory.read','memory.write','memory.delete')
        ON CONFLICT DO NOTHING
    """))

def downgrade() -> None:
    for name in ("ix_employee_memories_created_at", "ix_employee_memories_status", "ix_employee_memories_source_run_id", "ix_employee_memories_employee_id", "ix_employee_memories_tenant_id"):
        op.drop_index(name, table_name="employee_memories")
    op.drop_table("employee_memories")
