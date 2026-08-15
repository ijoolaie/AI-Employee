import pytest

from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError


def test_send_email_is_gated_and_side_effecting():
    tool = registry.get("send_email")
    assert tool.side_effects is True
    assert tool.requires_approval is True
    assert tool.required_permission == "run.execute"


@pytest.mark.asyncio
async def test_send_email_requires_approval():
    with pytest.raises(ValidationAppError) as exc:
        await registry.execute(
            "send_email",
            {"to": ["user@example.com"], "subject": "x", "body": "y"},
            permissions={"run.execute"},
            approval_granted=False,
        )
    assert exc.value.details["approval_required"] is True


@pytest.mark.asyncio
async def test_send_email_fails_closed_without_domain_allowlist(monkeypatch):
    from app.ai import tool_registry

    settings = tool_registry.get_settings()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from_email", "noreply@example.com")
    monkeypatch.setattr(settings, "smtp_allowed_recipient_domains", [])

    with pytest.raises(ValidationAppError, match="fail-closed"):
        await registry.execute(
            "send_email",
            {"to": ["user@example.com"], "subject": "x", "body": "y"},
            permissions={"run.execute"},
            approval_granted=True,
        )


@pytest.mark.asyncio
async def test_send_email_uses_smtp_after_approval(monkeypatch):
    from app.ai import tool_registry

    settings = tool_registry.get_settings()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_from_email", "noreply@example.com")
    monkeypatch.setattr(settings, "smtp_username", "")
    monkeypatch.setattr(settings, "smtp_password", None)
    monkeypatch.setattr(settings, "smtp_use_starttls", True)
    monkeypatch.setattr(settings, "smtp_allowed_recipient_domains", ["example.com"])

    class FakeSMTP:
        sent = None
        def __init__(self, host, port, timeout):
            assert host == "smtp.example.com"
            assert port == 587
            assert timeout == 20
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def starttls(self):
            pass
        def send_message(self, message):
            FakeSMTP.sent = message

    monkeypatch.setattr(tool_registry.smtplib, "SMTP", FakeSMTP)

    result = await registry.execute(
        "send_email",
        {"to": ["user@example.com"], "subject": "Hello", "body": "Approved test"},
        permissions={"run.execute"},
        approval_granted=True,
    )
    assert result["sent"] is True
    assert FakeSMTP.sent["Subject"] == "Hello"
    assert "Approved test" in FakeSMTP.sent.get_content()
