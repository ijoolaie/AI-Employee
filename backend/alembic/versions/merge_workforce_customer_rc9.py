"""Reconcile the post-v1.4.11 workforce/customer migration branch with the release head.

This migration is intentionally empty. It only joins the workforce/customer
RBAC branch rooted at customercustomerlifecycle to the established RC9
release head so fresh installs and upgrades have exactly one Alembic head.
"""

from __future__ import annotations

revision = "merge_workforce_customer_rc9"
down_revision = ("rc9merge04", "customercustomerlifecycle")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
