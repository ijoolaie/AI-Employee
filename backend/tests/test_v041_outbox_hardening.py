from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_email_outbox_dispatch_is_explicitly_queued_and_traced():
    source = (ROOT / "app/workers/outbox_worker.py").read_text()
    marker = 'OUTBOX_DISPATCH.labels("queued", row.kind).inc()'
    assert marker in source
    queued_block = source[source.index(marker):source.index("continue", source.index(marker))]
    assert 'current_span.set_attribute("outbox.status", "queued")' in queued_block


def test_non_email_outbox_dispatch_marks_dispatched():
    source = (ROOT / "app/workers/outbox_worker.py").read_text()
    assert "await outbox_service.mark_dispatched(db, row)" in source
    assert 'current_span.set_attribute("outbox.status", "dispatched")' in source
