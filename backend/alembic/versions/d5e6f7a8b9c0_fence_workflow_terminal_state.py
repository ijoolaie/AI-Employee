"""Prevent WorkflowRun terminal-state resurrection after timeout/cancellation/failure.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
"""
from alembic import op

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None

_TRIGGER_FUNCTION = "workflow_run_terminal_state_fence"
_TRIGGER = "trg_workflow_run_terminal_state_fence"


def upgrade() -> None:
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_TRIGGER_FUNCTION}()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF OLD.status IN ('success', 'failed', 'cancelled', 'timed_out')
               AND NEW.status <> OLD.status THEN
                RAISE EXCEPTION
                    'workflow_runs terminal state is immutable: % -> %',
                    OLD.status, NEW.status
                    USING ERRCODE = 'check_violation';
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER {_TRIGGER}
        BEFORE UPDATE OF status ON workflow_runs
        FOR EACH ROW
        EXECUTE FUNCTION {_TRIGGER_FUNCTION}();
        """
    )


def downgrade() -> None:
    op.execute(f"DROP TRIGGER IF EXISTS {_TRIGGER} ON workflow_runs")
    op.execute(f"DROP FUNCTION IF EXISTS {_TRIGGER_FUNCTION}()")
