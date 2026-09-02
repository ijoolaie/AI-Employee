"""Reconcile the post-RC9 development head with the canonical Phase 8.3 binding head.

This merge is intentionally created after the existing RC9 and Phase 12 migrations.
It preserves the historical RC9 lineage while bringing p8_03_agent_binding into the
single development migration head without rewriting an existing migration's ancestry.
"""

revision = "rc9p8merge01"
down_revision = ("p12_04_test_evidence", "p8_03_agent_binding")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
