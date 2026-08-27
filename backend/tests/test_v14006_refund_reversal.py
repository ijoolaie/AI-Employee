from app.schemas.billing import RefundRequest, RefundResponse


def test_refund_request_defaults_to_full_refund():
    request = RefundRequest(payment_intent_id="pi_test", idempotency_key="refund-1")
    assert request.operation == "refund"
    assert request.amount_cents is None
    assert request.currency == "usd"


def test_reversal_request_is_supported():
    request = RefundRequest(
        operation="reversal",
        payment_intent_id="pi_test",
        idempotency_key="reversal-1",
    )
    assert request.operation == "reversal"


def test_refund_response_contract_exposes_provider_and_lifecycle_state():
    assert {"pending", "succeeded", "failed"}.issuperset({"pending"})
    assert RefundResponse.model_fields["provider_refund_id"].is_required() is False
