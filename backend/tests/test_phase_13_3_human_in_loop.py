import uuid
from types import SimpleNamespace

import pytest

from app.services.approval_service import validate_resume_approval


def approval(**overrides):
    values = {
        "tenant_id": uuid.uuid4(),
        "run_id": uuid.uuid4(),
        "status": "approved",
        "tool_name": "create_order",
        "tool_call_id": "call-1",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_resume_approval_accepts_exact_grant():
    item = approval()
    validate_resume_approval(
        item,
        tenant_id=item.tenant_id,
        run_id=item.run_id,
        tool_name=item.tool_name,
        tool_call_id=item.tool_call_id,
    )


@pytest.mark.parametrize("status", ["pending", "rejected", "consumed"])
def test_resume_approval_rejects_non_current_status(status):
    item = approval(status=status)
    with pytest.raises(Exception, match="Approval is not currently granted"):
        validate_resume_approval(
            item,
            tenant_id=item.tenant_id,
            run_id=item.run_id,
            tool_name=item.tool_name,
            tool_call_id=item.tool_call_id,
        )


def test_resume_approval_rejects_tenant_mismatch():
    item = approval()
    with pytest.raises(Exception, match="does not match the Run tenant"):
        validate_resume_approval(
            item,
            tenant_id=uuid.uuid4(),
            run_id=item.run_id,
            tool_name=item.tool_name,
            tool_call_id=item.tool_call_id,
        )


def test_resume_approval_rejects_tool_call_mismatch():
    item = approval()
    with pytest.raises(Exception, match="does not match the requested tool call"):
        validate_resume_approval(
            item,
            tenant_id=item.tenant_id,
            run_id=item.run_id,
            tool_name=item.tool_name,
            tool_call_id="different-call",
        )
