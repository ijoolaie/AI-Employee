from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_send_email_cannot_bypass_transactional_outbox_without_tenant_context():
    source = (ROOT / "app/ai/tool_registry.py").read_text(encoding="utf-8")
    block = source[source.index('if name == "send_email"'):source.index('elif name == "analyze_dataset"')]
    assert 'if db is not None and tenant_id is not None:' in block
    assert 'send_email requires an active tenant Run context' in block
    assert 'smtplib.SMTP(' not in block
    assert 'from app.services.outbox_service import enqueue' in block
