from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_tenant_lifecycle_locks_authoritative_tenant_before_transition():
    source = (ROOT / "app/services/edition_lifecycle_service.py").read_text(encoding="utf-8")
    transition = source[source.index("async def transition_tenant_status"):source.index("async def set_child_tenant_status")]
    assert "select(Tenant).where(Tenant.id == tenant.id).with_for_update()" in transition
    assert "previous_status = tenant.status" in transition


def test_parent_deprovision_and_child_transition_share_child_row_lock():
    source = (ROOT / "app/services/edition_lifecycle_service.py").read_text(encoding="utf-8")
    transition = source[source.index("async def transition_tenant_status"):source.index("async def set_child_tenant_status")]
    child_transition = source[source.index("async def set_child_tenant_status"):]
    assert "select(Tenant).where(Tenant.parent_tenant_id == tenant.id).with_for_update()" in transition
    assert "select(Tenant).where(Tenant.id == child_id).with_for_update()" in child_transition
