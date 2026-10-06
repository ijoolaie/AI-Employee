from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW_SOURCE = (ROOT / "app/services/workflow_service.py").read_text(encoding="utf-8")
APPROVAL_SOURCE = (ROOT / "app/api/v1/workflow_approvals.py").read_text(encoding="utf-8")
TRIGGER_SOURCE = (ROOT / "app/workers/workflow_trigger_worker.py").read_text(encoding="utf-8")
TRIGGER_SERVICE_SOURCE = (ROOT / "app/services/workflow_trigger_service.py").read_text(encoding="utf-8")
RUN_SOURCE = (ROOT / "app/services/run_service.py").read_text(encoding="utf-8")
WORKER_SOURCE = (ROOT / "app/workers/workflow_worker.py").read_text(encoding="utf-8")


def test_cancel_child_creation_is_fail_closed():
    assert '.with_for_update()' in WORKFLOW_SOURCE
    assert 'Run.status.in_({"pending", "waiting"})' in WORKFLOW_SOURCE
    assert 'child.status in {"pending", "waiting"}' in WORKFLOW_SOURCE
    assert 'Run cancelled because its WorkflowRun became terminal before child execution' in WORKFLOW_SOURCE


def test_cancel_child_execution_is_fail_closed():
    assert 'if run.status in {"success", "failed", "cancelled", "running"}' in RUN_SOURCE
    assert 'if run.status != "running":' in WORKFLOW_SOURCE
    assert 'WORKFLOW_PARENT_NOT_RUNNING' not in WORKFLOW_SOURCE


def test_cancel_approval_cannot_resume_a_terminal_workflow():
    assert 'select(WorkflowRun)' in APPROVAL_SOURCE
    assert 'WorkflowRun.id == approval.workflow_run_id' in APPROVAL_SOURCE
    assert 'select(WorkflowStepRun)' in APPROVAL_SOURCE
    assert APPROVAL_SOURCE.index('select(WorkflowRun)') < APPROVAL_SOURCE.index('select(WorkflowStepRun)')
    assert '.with_for_update()' in APPROVAL_SOURCE[APPROVAL_SOURCE.index('select(WorkflowRun)'):APPROVAL_SOURCE.index('select(WorkflowStepRun)')]
    assert 'if run.status != "waiting_approval":' in APPROVAL_SOURCE
    assert 'await _enqueue_resume(db, run, reason=f"approval:{approval.id}")' in APPROVAL_SOURCE


def test_cancel_parallel_branch_clears_execution_lease():
    assert 'branch.execution_lease_id = None' in WORKFLOW_SOURCE
    assert 'branch.execution_lease_expires_at = None' in WORKFLOW_SOURCE
    assert 'branch.execution_heartbeat_at = None' in WORKFLOW_SOURCE
    assert 'branch.status = "cancelled" if parent.status == "cancelled" else "failed"' in WORKFLOW_SOURCE


def test_cancel_replay_stays_on_source_version_and_new_run_identity():
    assert 'source.workflow_version_id' in WORKFLOW_SOURCE
    assert 'wf["replay_of_run_id"] = str(source.id)' in WORKFLOW_SOURCE
    assert 'wf["replay_source_version_id"] = str(source.workflow_version_id)' in WORKFLOW_SOURCE


def test_timeout_child_completion_is_fenced_before_success_bookkeeping():
    assert 'if fresh_deadline and fresh_deadline <= datetime.now(timezone.utc):' in WORKFLOW_SOURCE
    assert 'run = await _lock_parent_for_child_execution(db, workflow_run_id=run.id)' in WORKFLOW_SOURCE
    assert 'run.status = "timed_out"' in WORKFLOW_SOURCE


def test_timeout_parallel_completion_is_fenced():
    assert 'parent = await _lock_parent_for_child_execution(db, workflow_run_id=parent.id)' in WORKFLOW_SOURCE
    assert 'if parent.status != "running":' in WORKFLOW_SOURCE
    assert 'branch.status = "cancelled" if parent.status == "cancelled" else "failed"' in WORKFLOW_SOURCE


def test_worker_crash_child_success_recovery_uses_durable_child_identity():
    assert 'durable_result = await db.execute(select(Run).where(Run.workflow_step_run_id == step.id))' in WORKFLOW_SOURCE
    assert 'if durable_child.status == "success":' in WORKFLOW_SOURCE
    assert 'WORKFLOW_CHILD_RETRY_UNSAFE' in WORKFLOW_SOURCE
    assert 'allow_recovery=True' in WORKFLOW_SOURCE


def test_worker_crash_branch_success_recovery_is_lease_fenced():
    assert 'recover_parallel_branch_execution_lease' in TRIGGER_SOURCE
    assert 'acquire_parallel_branch_execution_lease' in WORKFLOW_SOURCE
    assert 'assert_parallel_branch_execution_lease' in WORKFLOW_SOURCE


def test_replay_original_run_is_idempotent_and_does_not_reuse_execution_identity():
    assert 'idempotency_key=idempotency_key' in WORKFLOW_SOURCE
    assert 'run = await create_workflow_run(' in WORKFLOW_SOURCE
    assert 'replay_of_run_id' in WORKFLOW_SOURCE


def test_retry_existing_child_fails_closed():
    assert 'Linked employee Run ended with status' in WORKFLOW_SOURCE
    assert 'refusing to create a replacement Run' in WORKFLOW_SOURCE
    assert 'for attempt in range(1, max_attempts + 1)' not in WORKFLOW_SOURCE


def test_workflow_worker_does_not_blindly_celery_retry_execution_after_lease_loss():
    assert 'WORKFLOW_EXECUTION_LEASE_LOST' in WORKER_SOURCE
    execution_section = WORKER_SOURCE.split("def execute_workflow_task", 1)[0]
    assert 'raise self.retry(exc=exc' not in execution_section


def test_webhook_duplicate_ingestion_recovers_from_unique_race():
    assert 'IntegrityError' in TRIGGER_SERVICE_SOURCE
    assert 'uq_workflow_event_delivery_trigger_event' in TRIGGER_SERVICE_SOURCE
    assert 'await db.rollback()' in TRIGGER_SERVICE_SOURCE
    assert 'return delivery, False' in TRIGGER_SERVICE_SOURCE


def test_business_network_duplicate_request_recovers_from_unique_race():
    source = (ROOT / "app/services/business_network_service.py").read_text(encoding="utf-8")
    assert 'IntegrityError' in source
    assert 'uq_business_network_sender_idempotency' in source
    assert 'async with db.begin_nested()' in source
    assert 'return existing' in source


def test_commercial_license_issuance_serializes_on_tenant_row():
    source = (ROOT / "app/services/license_service.py").read_text(encoding="utf-8")
    assert 'select(Tenant).where(Tenant.id == tenant.id).with_for_update()' in source
    assert 'select(CommercialLicense).where(' in source
    assert 'CommercialLicense.tenant_id == tenant.id' in source


def test_agent_identity_creation_serializes_on_tenant_scoped_instance_row():
    source = Path("app/services/agent_governance.py").read_text()
    marker = "async def create_identity("
    block = source[source.index(marker):source.index("\n\nasync def review_access", source.index(marker))]
    assert "select(AgentInstance)" in block
    assert "AgentInstance.id == agent_instance_id" in block
    assert "AgentInstance.tenant_id == tenant_id" in block
    assert ".with_for_update()" in block


def test_schedule_creation_serializes_on_tenant_scoped_workflow_row():
    source = Path("app/services/workflow_trigger_service.py").read_text()
    marker = "async def create_schedule("
    block = source[source.index(marker):source.index("\n\nasync def claim_due_schedules", source.index(marker))]
    assert "select(Workflow)" in block
    assert "Workflow.id == workflow_id" in block
    assert "Workflow.tenant_id == tenant_id" in block
    assert ".with_for_update()" in block



def test_tenant_user_role_update_serializes_on_tenant_scoped_user_row():
    source = Path("app/api/v1/tenant_admin.py").read_text()
    marker = '@router.post("/users/{user_id}/roles"'
    block = source[source.index(marker):]
    assert "select(User)" in block
    assert "User.id == user_id" in block
    assert "User.tenant_id == ctx.tenant_id" in block
    assert ".with_for_update()" in block

def test_payout_destination_binding_serializes_on_seller_tenant_row():
    source = Path("app/services/skill_marketplace_payout_destination.py").read_text()
    marker = "async def bind_payout_destination("
    block = source[source.index(marker):source.index("\n\nasync def revoke_payout_destination", source.index(marker))]
    assert "select(Tenant)" in block
    assert "Tenant.id == seller_tenant_id" in block
    assert ".with_for_update()" in block


def test_entitlement_delegation_recovers_from_unique_race():
    source = Path("app/services/edition_service.py").read_text()
    marker = "async def delegate_entitlement("
    block = source[source.index(marker):source.index("\n\nasync def create_support_escalation", source.index(marker))]
    assert "IntegrityError" in block
    assert "async with db.begin_nested()" in block
    assert 'uq_tenant_entitlement_feature' in block
    assert "select(TenantEntitlement)" in block
    assert "row.quota_limit = effective_quota" in block


def test_child_tenant_provisioning_recovers_from_slug_unique_race():
    source = Path("app/services/edition_service.py").read_text()
    marker = "async def provision_child_tenant("
    block = source[source.index(marker):source.index("\n\nasync def _authorized_parent_entitlement", source.index(marker))]
    assert "async with db.begin_nested()" in block
    assert "IntegrityError" in block
    assert '"tenants_slug_key"' in block
    assert 'raise HTTPException(status_code=409, detail="Tenant slug already exists")' in block


def test_workforce_sla_upsert_recovers_only_expected_unique_race():
    source = (ROOT / "app/services/workforce_sla_service.py").read_text(encoding="utf-8")
    assert 'except IntegrityError as exc:' in source
    assert 'constraint_name != "uq_workforce_sla_contract_tenant"' in source
    assert 'if constraint_name != "uq_workforce_sla_contract_tenant":' in source
    assert '.with_for_update()' in source
