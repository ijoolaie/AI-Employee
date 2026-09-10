import pytest

from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError


def test_send_email_is_gated_and_side_effecting():
    tool = registry.get("send_email")
    assert tool.side_effects is True
    assert tool.requires_approval is True
    assert tool.required_permission == "run.execute"


@pytest.mark.asyncio
async def test_send_email_requires_transactional_tenant_context_before_approval():
    with pytest.raises(ValidationAppError, match="requires an active tenant Run context"):
        await registry.execute(
            "send_email",
            {"to": ["user@example.com"], "subject": "x", "body": "y"},
            permissions={"run.execute"},
            approval_granted=True,
        )


@pytest.mark.asyncio
async def test_send_email_cannot_bypass_side_effect_boundary_with_missing_tenant(monkeypatch):
    from app.ai import tool_registry

    settings = tool_registry.get_settings()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from_email", "noreply@example.com")
    monkeypatch.setattr(settings, "smtp_allowed_recipient_domains", ["example.com"])

    with pytest.raises(ValidationAppError, match="requires an active tenant Run context"):
        await registry.execute(
            "send_email",
            {"to": ["user@example.com"], "subject": "x", "body": "y"},
            permissions={"run.execute"},
            approval_granted=True,
        )
