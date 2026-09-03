"""Phase 12.5 Test Center active-run expiry sweep index.

Revision ID: p12_05_test_run_expiry_index
Revises: rc9p8merge01
"""

from alembic import op

revision = "p12_05_test_run_expiry_index"
down_revision = "rc9p8merge01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_test_runs_status_queued_started",
        "test_runs",
        ["status", "queued_at", "started_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_test_runs_status_queued_started", table_name="test_runs")
