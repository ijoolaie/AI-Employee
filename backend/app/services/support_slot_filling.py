"""Deterministic slot requirements for customer-support conversations.

This module is policy-only: it never invents prices, stock, delivery times,
refunds, or escalation success. Callers must supply trusted slots and policy.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class SlotDecision:
    intent: str
    missing_slots: tuple[str, ...]
    next_question: str | None
    can_answer_from_policy: bool
    reason: str

_QUESTIONS = {
    "city": "ارسال برای کدوم شهره؟ 😊",
    "order_id": "شماره سفارش‌تون رو می‌فرمایید؟",
    "payment_reference": "شماره پیگیری پرداخت یا سفارش رو می‌فرمایید؟",
    "product": "کدوم محصول مدنظرتونه؟",
    "color": "چه رنگی مدنظرتونه؟",
    "size": "چه سایزی می‌خواید؟",
    "quantity": "چند عدد مدنظرتونه؟",
    "reason": "دلیل درخواست تعویض یا مرجوعی رو می‌فرمایید؟",
    "issue_details": "ممکنه کمی بیشتر درباره مشکلی که پیش اومده توضیح بدید؟",
}
_REQUIRED_SLOTS = {
    "shipping_fee": ("city",),
    "delivery_eta": ("city", "order_id"),
    "variant_stock": ("product", "color", "size"),
    "bulk_discount": ("product", "quantity"),
    "return_exchange": ("order_id", "reason"),
    "payment_issue": ("order_id", "payment_reference"),
    "damaged_order": ("order_id", "issue_details"),
}

def plan_support_turn(*, intent: str, known_slots: dict[str, Any] | None = None,
                      policy: dict[str, Any] | None = None) -> SlotDecision:
    """Plan the next required question without fabricating a business answer."""
    slots = known_slots or {}
    trusted_policy = policy or {}
    if intent not in _REQUIRED_SLOTS:
        return SlotDecision(intent, (), None, False, "unknown_intent_requires_review")
    required = list(_REQUIRED_SLOTS[intent])
    if intent == "shipping_fee":
        shipping = trusted_policy.get("shipping")
        if isinstance(shipping, dict) and shipping.get("flat_rate_all_destinations") is True:
            required = []
    missing = tuple(slot for slot in required if slots.get(slot) is None or
                    (isinstance(slots.get(slot), str) and not slots[slot].strip()))
    if missing:
        return SlotDecision(intent, missing, _QUESTIONS.get(missing[0]), False,
                            "required_context_missing")
    if intent == "shipping_fee":
        shipping = trusted_policy.get("shipping")
        has_rate = isinstance(shipping, dict) and (
            shipping.get("flat_rate_all_destinations") is True or shipping.get("rates_by_city"))
        return SlotDecision(intent, (), None, bool(has_rate),
                            "trusted_shipping_policy_available" if has_rate else "shipping_policy_unavailable")
    if intent == "delivery_eta":
        sla = trusted_policy.get("delivery_sla_by_city")
        has_sla = isinstance(sla, dict) and bool(sla.get(slots.get("city")))
        return SlotDecision(intent, (), None, has_sla,
                            "trusted_delivery_sla_available" if has_sla else "delivery_sla_unavailable")
    policy_key = {"variant_stock": "stock", "bulk_discount": "discounts",
                  "return_exchange": "returns", "payment_issue": "payment_status",
                  "damaged_order": "damage_resolution"}[intent]
    available = policy_key in trusted_policy and trusted_policy[policy_key] is not None
    return SlotDecision(intent, (), None, bool(available),
                        "trusted_policy_available" if available else "policy_or_authorized_review_required")
