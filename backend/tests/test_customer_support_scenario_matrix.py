"""Scenario matrix for deterministic customer-support slot preflight.

These tests exercise the same preflight entry point used by RunService. They
verify the minimum required question at each turn; trusted business answers
remain gated by the channel policy and the model's support contract.
"""
import pytest

from app.services.support_slot_filling import support_slot_preflight_response


@pytest.mark.parametrize(
    ("message", "policy", "turns"),
    [
        (
            "هزینه ارسال چقدر است؟",
            {"shipping": {"rates_by_city": {"تهران": 50000}}},
            [
                ({}, "ارسال برای کدوم شهره؟ 😊"),
                ({"city": "تهران"}, None),
            ],
        ),
        (
            "زمان تحویل سفارش من چقدره؟",
            {"delivery_sla_by_city": {"تهران": "۱ تا ۲ روز کاری"}},
            [
                ({}, "ارسال برای کدوم شهره؟ 😊"),
                ({"city": "تهران"}, "شماره سفارش‌تون رو می‌فرمایید؟"),
                ({"city": "تهران", "order_id": "ORD-ETA-1"}, None),
            ],
        ),
        (
            "موجودی تی‌شرت در چه رنگ و سایزی هست؟",
            {"stock": {"تی‌شرت": {"آبی": {"M": 3}}}},
            [
                ({"product": "تی‌شرت"}, "چه رنگی مدنظرتونه؟"),
                ({"product": "تی‌شرت", "color": "آبی"}, "چه سایزی می‌خواید؟"),
                ({"product": "تی‌شرت", "color": "آبی", "size": "M"}, None),
            ],
        ),
        (
            "برای خرید عمده تخفیف دارید؟",
            {"discounts": {"bulk_minimum": 10}},
            [
                ({"product": "تی‌شرت"}, "چند عدد مدنظرتونه؟"),
                ({"product": "تی‌شرت", "quantity": 20}, None),
            ],
        ),
        (
            "می‌خوام کالا رو مرجوع کنم",
            {"returns": {"review_required": True}},
            [
                ({"order_id": "ORD-RET-1"}, "دلیل درخواست تعویض یا مرجوعی رو می‌فرمایید؟"),
                ({"order_id": "ORD-RET-1", "reason": "کالای آسیب‌دیده"}, None),
            ],
        ),
        (
            "پرداخت من ناموفق بوده",
            {"payment_status": {"lookup_required": True}},
            [
                ({"order_id": "ORD-PAY-1"}, "شماره پیگیری پرداخت یا سفارش رو می‌فرمایید؟"),
                ({"order_id": "ORD-PAY-1", "payment_reference": "PAY-1001"}, None),
            ],
        ),
        (
            "سفارشم آسیب دیده",
            {"damage_resolution": {"review_required": True}},
            [
                ({"order_id": "ORD-DMG-1"}, "ممکنه کمی بیشتر درباره مشکلی که پیش اومده توضیح بدید؟"),
                ({"order_id": "ORD-DMG-1", "issue_details": "بسته شکسته رسیده"}, None),
            ],
        ),
    ],
)
def test_support_scenario_matrix_asks_only_the_next_missing_detail(
    message, policy, turns
):
    for known_slots, expected in turns:
        assert support_slot_preflight_response(
            message,
            policy,
            known_slots=known_slots,
        ) == expected


@pytest.mark.parametrize(
    ("message", "policy", "known_slots", "expected_fragment"),
    [
        (
            "هزینه ارسال به شیراز چقدر است؟",
            {"shipping": {"cities": ["شیراز"], "rates_by_city": {"تهران": 50000}}},
            {},
            "نرخ ارسالِ تأییدشده‌ای",
        ),
        (
            "زمان تحویل سفارش من چقدره؟",
            {},
            {"city": "تهران", "order_id": "ORD-ETA-2"},
            None,
        ),
        (
            "پرداخت من ناموفق بوده",
            {},
            {"order_id": "ORD-PAY-2", "payment_reference": "PAY-2002"},
            None,
        ),
    ],
)
def test_completed_slots_continue_to_policy_guarded_model_path(
    message, policy, known_slots, expected_fragment
):
    response = support_slot_preflight_response(message, policy, known_slots=known_slots)
    if expected_fragment is None:
        assert response is None
    else:
        assert response is not None
        assert expected_fragment in response
