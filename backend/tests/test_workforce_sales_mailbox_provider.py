import email
import uuid

from app.services import workforce_sales_mailbox_provider as provider


def test_message_ids_extracts_rfc_message_ids():
    value = '<outbox-123@ai-employee.local> <other@example.test>'
    assert provider._message_ids(value) == {
        'outbox-123@ai-employee.local',
        'other@example.test',
    }


def test_message_ids_accepts_provider_normalized_unbracketed_ids():
    value = "outbox-123@ai-employee.local other@example.test"
    assert provider._message_ids(value) == {
        "outbox-123@ai-employee.local",
        "other@example.test",
    }


def test_response_text_reads_plain_text_part():
    message = email.message_from_string(
        'From: prospect@example.test\n'
        'Subject: Re: pricing\n'
        'Message-ID: <reply-1@example.test>\n'
        'In-Reply-To: <outbox-123@ai-employee.local>\n'
        '\n'
        'Please send pricing.\n'
    )
    assert provider._response_text(message) == 'Please send pricing.'


def test_mailbox_response_contract():
    response = provider.MailboxResponse(
        tenant_id=uuid.uuid4(),
        provider_message_id='outbox-123',
        event_id='message:reply-1@example.test',
        response_text='Interested.',
        sender='prospect@example.test',
        subject='Re: pricing',
    )
    assert response.provider_message_id == 'outbox-123'
    assert response.event_id.startswith('message:')
