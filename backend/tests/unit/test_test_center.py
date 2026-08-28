from uuid import uuid4

import pytest

from app.services.test_center import TestCenterError, TestCenterService, TestRun


def test_safe_mode_rejects_mutation():
    tenant = uuid4()
    run = TestRun(tenant_id=tenant, actor_id=uuid4(), family="workflow", mutation_requested=True)

    with pytest.raises(TestCenterError, match="safe mode"):
        TestCenterService().start(run, actor_tenant_id=tenant)


def test_test_center_preserves_tenant_and_exports_evidence():
    tenant = uuid4()
    run = TestRun(tenant_id=tenant, actor_id=uuid4(), family="handoff")
    service = TestCenterService()

    service.start(run, actor_tenant_id=tenant)
    service.complete(run, passed=True, evidence={"check": "tenant-isolation"})

    exported = service.export_evidence(run)
    assert exported["tenant_id"] == str(tenant)
    assert exported["status"] == "passed"
    assert exported["evidence"][-1]["check"] == "tenant-isolation"


def test_test_center_rejects_cross_tenant_actor():
    run = TestRun(tenant_id=uuid4(), actor_id=uuid4(), family="agent")
    with pytest.raises(TestCenterError, match="tenant mismatch"):
        TestCenterService().start(run, actor_tenant_id=uuid4())
