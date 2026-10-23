import pytest
from app.services.support_slot_filling import find_trusted_shipping_city, plan_support_turn

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
