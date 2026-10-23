"""Deterministic acceptance coverage for customer-support slot filling.

These tests verify only the planner contract. They do not claim end-to-end
LLM, storefront-policy, or production-channel acceptance.
"""
import pytest

from app.services.support_slot_filling import (
    find_trusted_shipping_city,
    plan_support_turn,
)


@pytest.mark.parametrize(
    ("intent", "known_slots", "expected_missing", "expected_question"),
    [
        ("shipping_fee", {}, ("city",), "ارسال برای کدوم شهره؟ 😊"),
        ("delivery_eta", {}, ("city", "order_id"), "ارسال برای کدوم شهره؟ 😊"),
        (
            "variant_stock",
            {"product": "کتاب الف"},
            ("color", "size"),
            "چه رنگی مدنظرتونه؟",
        ),
        (
            "bulk_discount",
            {"product": "کتاب الف"},
            ("quantity",),
            "چند عدد مدنظرتونه؟",
        ),
        (
            "return_exchange",
            {"order_id": "ORD-123"},
            ("reason",),
            "دلیل درخواست تعویض یا مرجوعی رو می‌فرمایید؟",
        ),
        (
            "payment_issue",
            {"order_id": "ORD-123"},
            ("payment_reference",),
            "شماره پیگیری پرداخت یا سفارش رو می‌فرمایید؟",
        ),
        (
            "damaged_order",
            {"order_id": "ORD-123"},
            ("issue_details",),
            "ممکنه کمی بیشتر درباره مشکلی که پیش اومده توضیح بدید؟",
        ),
    ],
)
def test_planner_asks_only_for_first_missing_required_slot(
    intent, known_slots, expected_missing, expected_question
):
    decision = plan_support_turn(intent=intent, known_slots=known_slots)

    assert decision.missing_slots == expected_missing
    assert decision.next_question == expected_question
    assert decision.can_answer_from_policy is False
    assert decision.reason == "required_context_missing"


def test_shipping_fee_does_not_invent_rate_when_city_is_known_but_policy_missing():
    decision = plan_support_turn(
        intent="shipping_fee",
        known_slots={"city": "تهران"},
        policy={},
    )

    assert decision.missing_slots == ()
    assert decision.next_question is None
    assert decision.can_answer_from_policy is False
    assert decision.reason == "shipping_policy_unavailable"


def test_flat_rate_shipping_policy_does_not_require_city():
    decision = plan_support_turn(
        intent="shipping_fee",
        policy={"shipping": {"flat_rate_all_destinations": True, "flat_rate": 80000}},
    )

    assert decision.missing_slots == ()
    assert decision.next_question is None
    assert decision.can_answer_from_policy is True
    assert decision.reason == "trusted_shipping_policy_available"


def test_city_match_uses_only_configured_city_names_and_prefers_longest_match():
    policy = {
        "rates_by_city": {"تهران": 50000, "تهرانپارس": 70000},
        "cities": ["کرج"],
    }

    assert find_trusted_shipping_city("هزینه ارسال به تهرانپارس چقدره؟", policy) == "تهرانپارس"
    assert find_trusted_shipping_city("ارسال برای کرج", policy) == "کرج"
    assert find_trusted_shipping_city("ارسال به اصفهان", policy) is None


def test_unknown_intent_requires_review_instead_of_guessing():
    decision = plan_support_turn(intent="refund_me_now", known_slots={})

    assert decision.missing_slots == ()
    assert decision.next_question is None
    assert decision.can_answer_from_policy is False
    assert decision.reason == "unknown_intent_requires_review"
