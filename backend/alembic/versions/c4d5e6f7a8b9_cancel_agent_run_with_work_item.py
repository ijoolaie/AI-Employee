"""Cancel pending Agent Runs when their WorkItem is cancelled.
Revision ID: c4d5e6f7a8b9
Revises: 0a1b2c3d4e5f, v14013billingmanagementrbac
"""
from alembic import op

revision = "c4d5e6f7a8b9"
down_revision = ("0a1b2c3d4e5f", "v14013billingmanagementrbac")
branch_labels = None
depends_on = None


TRIGGER_NAME = "trg_work_items_cancel_agent_run"
FUNCTION_NAME = "cancel_agent_run_for_work_item"


def upgrade():
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {FUNCTION_NAME}()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NEW.status = 'cancelled' AND OLD.status IS DISTINCT FROM NEW.status
               AND NEW.executor_type = 'agent'
               AND NEW.output_data ? 'run_id' THEN
                UPDATE runs
                   SET status = 'cancelled',
                       completed_at = COALESCE(completed_at, NOW()),
                       error = jsonb_build_object(
                           'code', 'RUN_CANCELLED',
                           'message', 'Run cancelled with its WorkItem before execution started'
                       )
                 WHERE id = (NEW.output_data ->> 'run_id')::uuid
                   AND tenant_id = NEW.tenant_id
                   AND status IN ('pending', 'waiting');
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        f"""
        DROP TRIGGER IF EXISTS {TRIGGER_NAME} ON work_items;
        CREATE TRIGGER {TRIGGER_NAME}
        AFTER UPDATE OF status ON work_items
        FOR EACH ROW
        EXECUTE FUNCTION {FUNCTION_NAME}();
        """
    )


def downgrade():
    op.execute(f"DROP TRIGGER IF EXISTS {TRIGGER_NAME} ON work_items;")
    op.execute(f"DROP FUNCTION IF EXISTS {FUNCTION_NAME}();")
