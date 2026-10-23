import pytest
from app.services.support_slot_filling import current_customer_message_for_preflight, find_trusted_shipping_city, has_valid_flat_shipping_rate, plan_support_turn, shipping_fee_preflight_response

def test_shipping_fee_asks_city_before_answering():
    d = plan_support_turn(intent="shipping_fee")
    assert d.missing_slots == ("city",)
    assert d.next_question == "ارسال برای کدوم شهره؟ 😊"
    assert not d.can_answer_from_policy

def test_shipping_fee_uses_known_city_without_reasking():
    d = plan_support_turn(intent="shipping_fee", known_slots={"city": "تهران"},
                          policy={"shipping": {"rates_by_city": {"تهران": 65000}}})
    assert d.missing_slots == ()
    assert d.can_answer_from_policy

def test_flat_rate_policy_does_not_ask_city():
    d = plan_support_turn(intent="shipping_fee",
                          policy={"shipping": {"flat_rate_all_destinations": True, "amount": 50000}})
    assert d.missing_slots == ()
    assert d.can_answer_from_policy

def test_known_city_without_rate_does_not_authorize_guess():
    d = plan_support_turn(intent="shipping_fee", known_slots={"city": "تهران"})
    assert not d.can_answer_from_policy
    assert d.reason == "shipping_policy_unavailable"

def test_eta_asks_city_then_order_reference():
    d = plan_support_turn(intent="delivery_eta")
    assert d.missing_slots == ("city", "order_id")
    assert d.next_question == "ارسال برای کدوم شهره؟ 😊"
    d = plan_support_turn(intent="delivery_eta", known_slots={"city": "شیراز"})
    assert d.missing_slots == ("order_id",)
    assert d.next_question == "شماره سفارش‌تون رو می‌فرمایید؟"

def test_eta_needs_trusted_sla():
    d = plan_support_turn(intent="delivery_eta", known_slots={"city": "تهران", "order_id": "ORD-100"})
    assert not d.can_answer_from_policy
    assert d.reason == "delivery_sla_unavailable"

@pytest.mark.parametrize(("intent", "known", "missing", "question"), [
    ("variant_stock", {"product": "تی‌شرت"}, ("color", "size"), "چه رنگی مدنظرتونه؟"),
    ("bulk_discount", {"product": "تی‌شرت"}, ("quantity",), "چند عدد مدنظرتونه؟"),
    ("return_exchange", {"order_id": "ORD-1"}, ("reason",), "دلیل درخواست تعویض یا مرجوعی رو می‌فرمایید؟"),
    ("payment_issue", {"order_id": "ORD-1"}, ("payment_reference",), "شماره پیگیری پرداخت یا سفارش رو می‌فرمایید؟"),
    ("damaged_order", {"order_id": "ORD-1"}, ("issue_details",), "ممکنه کمی بیشتر درباره مشکلی که پیش اومده توضیح بدید؟"),
])
def test_asks_only_first_missing_slot(intent, known, missing, question):
    d = plan_support_turn(intent=intent, known_slots=known)
    assert d.missing_slots == missing
    assert d.next_question == question
    assert not d.can_answer_from_policy

def test_known_slots_do_not_imply_discount_policy():
    d = plan_support_turn(intent="bulk_discount", known_slots={"product": "تی‌شرت", "quantity": 2})
    assert d.missing_slots == ()
    assert d.next_question is None
    assert not d.can_answer_from_policy

def test_unknown_intent_requires_review():
    d = plan_support_turn(intent="refund_everything")
    assert not d.can_answer_from_policy
    assert d.reason == "unknown_intent_requires_review"


@pytest.mark.parametrize(("message", "policy", "expected"), [
    ("هزینه ارسال به تهران چقدر است؟", {"rates_by_city": {"تهران": 65000}}, "تهران"),
    ("هزینه ارسال به شیراز", {"cities": ["تهران", "شیراز"]}, "شیراز"),
    ("هزینه ارسال به تبریز", {"known_cities": ["تهران"]}, None),
    ("هزینه ارسال به تهران", {"cities": "تهران"}, None),
    ("هزینه ارسال به تهران", None, None),
])
def test_find_trusted_shipping_city_uses_only_configured_city_names(message, policy, expected):
    assert find_trusted_shipping_city(message, policy) == expected


def test_find_trusted_shipping_city_prefers_longest_matching_name():
    assert find_trusted_shipping_city(
        "هزینه ارسال به شهرکرد",
        {"known_cities": ["شهر", "شهرکرد"]},
    ) == "شهرکرد"


def test_known_city_does_not_imply_shipping_rate():
    city = find_trusted_shipping_city("هزینه ارسال به تهران", {"cities": ["تهران"]})
    decision = plan_support_turn(intent="shipping_fee", known_slots={"city": city}, policy={})
    assert city == "تهران"
    assert not decision.can_answer_from_policy
    assert decision.reason == "shipping_policy_unavailable"


# Additional acceptance edge cases; keep the original regression cases above intact.

def test_shipping_fee_without_policy_does_not_invent_rate():
    decision = plan_support_turn(
        intent="shipping_fee", known_slots={"city": "تهران"}, policy={}
    )
    assert decision.missing_slots == ()
    assert decision.next_question is None
    assert decision.can_answer_from_policy is False
    assert decision.reason == "shipping_policy_unavailable"


def test_city_match_prefers_longest_configured_name():
    policy = {"rates_by_city": {"تهران": 50000}, "cities": ["تهرانپارس", "کرج"]}
    assert find_trusted_shipping_city("ارسال به تهرانپارس", policy) == "تهرانپارس"
    assert find_trusted_shipping_city("ارسال به اصفهان", policy) is None


def test_unknown_intent_requires_review_without_guessing():
    decision = plan_support_turn(intent="refund_me_now", known_slots={})
    assert decision.missing_slots == ()
    assert decision.next_question is None
    assert decision.can_answer_from_policy is False
    assert decision.reason == "unknown_intent_requires_review"


def test_empty_string_is_treated_as_missing_slot():
    decision = plan_support_turn(
        intent="shipping_fee", known_slots={"city": "   "}, policy={}
    )
    assert decision.missing_slots == ("city",)
    assert decision.next_question == "ارسال برای کدوم شهره؟ 😊"
    assert decision.can_answer_from_policy is False

def test_shipping_fee_does_not_use_another_citys_rate():
    decision = plan_support_turn(
        intent="shipping_fee",
        known_slots={"city": "شیراز"},
        policy={"shipping": {"rates_by_city": {"تهران": 65000}}},
    )
    assert not decision.can_answer_from_policy
    assert decision.reason == "shipping_policy_unavailable"


@pytest.mark.parametrize("rate", [None, "", "   "])
def test_shipping_fee_rejects_missing_or_blank_city_rate(rate):
    decision = plan_support_turn(
        intent="shipping_fee",
        known_slots={"city": "تهران"},
        policy={"shipping": {"rates_by_city": {"تهران": rate}}},
    )
    assert not decision.can_answer_from_policy
    assert decision.reason == "shipping_policy_unavailable"


def test_flat_rate_flag_without_amount_does_not_authorize_answer():
    decision = plan_support_turn(
        intent="shipping_fee",
        policy={"shipping": {"flat_rate_all_destinations": True}},
    )
    assert decision.missing_slots == ("city",)
    assert not decision.can_answer_from_policy


def test_flat_rate_with_amount_applies_without_city():
    decision = plan_support_turn(
        intent="shipping_fee",
        policy={"shipping": {"flat_rate_all_destinations": True, "amount": 0}},
    )
    assert decision.missing_slots == ()
    assert decision.can_answer_from_policy



@pytest.mark.parametrize(
    ("policy", "expected"),
    [
        ({"flat_rate_all_destinations": True, "amount": 50000}, True),
        ({"flat_rate_all_destinations": True, "amount": 0}, True),
        ({"flat_rate_all_destinations": True, "amount": None}, False),
        ({"flat_rate_all_destinations": True, "amount": ""}, False),
        ({"flat_rate_all_destinations": True, "amount": "   "}, False),
        ({"flat_rate_all_destinations": False, "amount": 50000}, False),
        ({"amount": 50000}, False),
        (None, False),
    ],
)
def test_flat_shipping_rate_requires_explicit_flag_and_nonblank_amount(policy, expected):
    assert has_valid_flat_shipping_rate(policy) is expected


def test_shipping_preflight_asks_city_when_destination_is_unknown():
    assert shipping_fee_preflight_response(
        "هزینه ارسال چقدر است؟",
        {"shipping": {"rates_by_city": {"تهران": 50000}}},
    ) == "ارسال برای کدوم شهره؟ 😊"


def test_shipping_preflight_does_not_let_model_guess_missing_city_rate():
    response = shipping_fee_preflight_response(
        "هزینه ارسال به شیراز چقدر است؟",
        {"shipping": {"cities": ["شیراز"], "rates_by_city": {"تهران": 50000}}},
    )
    assert response is not None
    assert "نرخ ارسالِ تأییدشده‌ای" in response


def test_shipping_preflight_allows_configured_city_rate():
    assert shipping_fee_preflight_response(
        "هزینه ارسال به تهران چقدر است؟",
        {"shipping": {"rates_by_city": {"تهران": 50000}, "cities": ["تهران"]}},
    ) is None


def test_shipping_preflight_does_not_accept_flat_rate_flag_without_amount():
    response = shipping_fee_preflight_response(
        "هزینه ارسال چقدر است؟",
        {"shipping": {"flat_rate_all_destinations": True}},
    )
    assert response == "ارسال برای کدوم شهره؟ 😊"




def test_preflight_uses_current_turn_not_shipping_terms_in_prior_transcript():
    current_message = "\u0645\u06cc\u200c\u062e\u0648\u0627\u0647\u0645 \u06a9\u0627\u0644\u0627\u06cc \u0622\u0633\u06cc\u0628\u200c\u062f\u06cc\u062f\u0647 \u0631\u0627 \u0645\u0631\u062c\u0648\u0639 \u06a9\u0646\u0645"
    input_data = {
        "message": "Current customer message: " + current_message + "\n\nPrevious conversation transcript: \u0647\u0632\u06cc\u0646\u0647 \u0627\u0631\u0633\u0627\u0644 \u0686\u0642\u062f\u0631\u0647\u061f",
        "current_customer_message": current_message,
    }
    current = current_customer_message_for_preflight(input_data)
    assert current == current_message
    assert shipping_fee_preflight_response(current, {"shipping": {"rates_by_city": {"\u062a\u0647\u0631\u0627\u0646": 50000}}}) is None


def test_preflight_does_not_reuse_city_from_prior_transcript():
    current_message = "\u0647\u0632\u06cc\u0646\u0647 \u0627\u0631\u0633\u0627\u0644 \u0686\u0642\u062f\u0631\u0647\u061f"
    input_data = {
        "message": "Current customer message: " + current_message + "\n\nPrevious conversation transcript: Customer: \u062a\u0647\u0631\u0627\u0646",
        "current_customer_message": current_message,
    }
    current = current_customer_message_for_preflight(input_data)
    assert current == current_message
    assert shipping_fee_preflight_response(current, {"shipping": {"rates_by_city": {"\u062a\u0647\u0631\u0627\u0646": 50000}}}) == "\u0627\u0631\u0633\u0627\u0644 \u0628\u0631\u0627\u06cc \u06a9\u062f\u0648\u0645 \u0634\u0647\u0631\u0647\u061f \U0001f60a"


def test_preflight_message_selector_falls_back_for_legacy_runs():
    assert current_customer_message_for_preflight({"message": "legacy message"}) == "legacy message"
