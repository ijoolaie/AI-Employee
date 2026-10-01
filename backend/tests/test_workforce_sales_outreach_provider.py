import pytest

from app.services import workforce_sales_outreach_provider


@pytest.mark.asyncio
async def test_sales_outreach_fails_closed_when_provider_is_none(monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "sales_outreach_provider_name", "none")

    result = await workforce_sales_outreach_provider.execute_sales_outreach(
        db=None,
        tenant_id="tenant-1",
        arguments={
            "to": ["prospect@example.com"],
            "subject": "Hello",
            "message": "Test",
        },
        tool_call_id="call-1",
    )

    assert result["provider_execution"] == "not_configured"
    assert result["executed"] is False
    assert result["external_side_effect"] is False


@pytest.mark.asyncio
async def test_sales_outreach_smtp_queues_through_transactional_outbox(monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "sales_outreach_provider_name", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from_email", "sales@example.com")
    monkeypatch.setattr(settings, "smtp_allowed_recipient_domains", ["example.com"])

    captured = {}

    class Queued:
        id = "outbox-1"

    async def fake_enqueue(db, *, kind, tenant_id, dedupe_key, payload):
        captured.update(
            db=db,
            kind=kind,
            tenant_id=tenant_id,
            dedupe_key=dedupe_key,
            payload=payload,
        )
        return Queued()

    monkeypatch.setattr(
        workforce_sales_outreach_provider.outbox_service,
        "enqueue",
        fake_enqueue,
    )

    result = await workforce_sales_outreach_provider.execute_sales_outreach(
        db=object(),
        tenant_id="tenant-1",
        arguments={
            "to": ["prospect@example.com"],
            "subject": "Hello",
            "message": "Test",
        },
        tool_call_id="call-1",
    )

    assert result["provider_execution"] == "queued"
    assert result["executed"] is True
    assert result["external_side_effect"] is True
    assert result["outbox_id"] == "outbox-1"
    assert captured["kind"] == "email.send"
    assert captured["tenant_id"] == "tenant-1"
    assert captured["dedupe_key"] == "sales-outreach:call-1"
    assert captured["payload"]["to"] == ["prospect@example.com"]


@pytest.mark.asyncio
async def test_sales_outreach_rejects_recipient_outside_operator_allowlist(monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "sales_outreach_provider_name", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from_email", "sales@example.com")
    monkeypatch.setattr(settings, "smtp_allowed_recipient_domains", ["example.com"])

    with pytest.raises(Exception, match="Recipient domain is not allowed"):
        await workforce_sales_outreach_provider.execute_sales_outreach(
            db=object(),
            tenant_id="tenant-1",
            arguments={
                "to": ["outside@other.example"],
                "subject": "Hello",
                "message": "Test",
            },
            tool_call_id="call-1",
        )
