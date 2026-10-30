"""Deterministic slot requirements for customer-support conversations.

This module is policy-only: it never invents prices, stock, delivery times,
refunds, or escalation success. Callers must supply trusted slots and policy.
"""
from __future__ import annotations

import re
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

def has_valid_flat_shipping_rate(shipping_policy: dict[str, Any] | None) -> bool:
    """Whether trusted shipping config defines a usable all-destination rate."""
    if not isinstance(shipping_policy, dict):
        return False
    amount = shipping_policy.get("amount")
    return (
        shipping_policy.get("flat_rate_all_destinations") is True
        and amount is not None
        and (not isinstance(amount, str) or bool(amount.strip()))
    )

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
        has_flat_rate = has_valid_flat_shipping_rate(shipping)
        if has_flat_rate:
            required = []
    missing = tuple(slot for slot in required if slots.get(slot) is None or
                    (isinstance(slots.get(slot), str) and not slots[slot].strip()))
    if missing:
        return SlotDecision(intent, missing, _QUESTIONS.get(missing[0]), False,
                            "required_context_missing")
    if intent == "shipping_fee":
        shipping = trusted_policy.get("shipping")
        has_rate = False
        if isinstance(shipping, dict):
            has_flat_rate = has_valid_flat_shipping_rate(shipping)
            rates_by_city = shipping.get("rates_by_city")
            city = slots.get("city")
            city_rate = rates_by_city.get(city) if isinstance(rates_by_city, dict) else None
            has_city_rate = (
                city_rate is not None
                and (not isinstance(city_rate, str) or bool(city_rate.strip()))
            )
            has_rate = has_flat_rate or has_city_rate
        return SlotDecision(intent, (), None, has_rate,
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



# Conservative phrases only: ambiguous or unrecognized requests stay on the
# normal guarded model path rather than being assigned a guessed intent.
_INTENT_PHRASES = {
    "shipping_fee": ("هزینه ارسال", "هزینه‌ی ارسال", "هزینه پست", "کرایه ارسال",
                     "قیمت ارسال", "ارسال چقدر", "ارسال چند", "هزینه حمل"),
    "delivery_eta": ("زمان تحویل", "کی میرسه", "کی میرسد", "چند روزه میرسه",
                     "مدت زمان ارسال", "زمان رسیدن سفارش", "delivery eta", "when will it arrive"),
    "variant_stock": ("موجودی", "موجوده", "موجود دارید", "چه رنگی", "چه سایزی",
                      "رنگ و سایز", "stock availability", "available in"),
    "bulk_discount": ("تخفیف عمده", "تخفیف تعداد", "خرید عمده", "تعداد بالا",
                      "قیمت عمده", "bulk discount", "wholesale discount"),
    "return_exchange": ("مرجوع", "تعویض کالا", "تعویضش کنم", "پس بدم", "پس بفرستم",
                        "return this", "exchange this"),
    "payment_issue": ("مشکل پرداخت", "پرداختم", "پرداخت ناموفق", "پرداخت من ناموفق", "واریز کردم",
                      "پول کم شده", "کسر شده", "تراکنش", "payment issue", "payment failed"),
    "damaged_order": ("آسیب دیده", "آسیب‌دیده", "شکسته رسیده", "خراب رسیده",
                      "کالای معیوب", "خرابی کالا", "damaged item", "arrived broken"),
}


def detect_support_intent(message: str) -> str | None:
    """Recognize only explicit support-intent phrases; return None on ambiguity."""
    if not isinstance(message, str) or not message.strip():
        return None
    normalized = " ".join(
        message.casefold().replace("\u064a", "\u06cc").replace("\u0643", "\u06a9")
        .replace("\u200c", " ").split()
    )
    matches = [
        intent for intent, phrases in _INTENT_PHRASES.items()
        if any(
            " ".join(phrase.casefold().replace("\u200c", " ").split()) in normalized
            for phrase in phrases
        )
    ]
    return matches[0] if len(matches) == 1 else None


def find_trusted_shipping_city(message: str, shipping_policy: dict[str, Any] | None = None) -> str | None:
    """Return a configured city explicitly mentioned by the customer, if any.

    Only trusted policy keys/lists are considered. This helper identifies context;
    it does not imply that a shipping rate exists for the matched city.
    """
    policy = shipping_policy if isinstance(shipping_policy, dict) else {}
    rates_by_city = policy.get("rates_by_city", {})
    rates_by_city = rates_by_city if isinstance(rates_by_city, dict) else {}
    known_cities = policy.get("cities", policy.get("known_cities", []))
    known_cities = known_cities if isinstance(known_cities, list) else []
    message_folded = message.casefold()
    candidates = [city for city in [*rates_by_city.keys(), *known_cities]
                  if isinstance(city, str) and city.strip()]
    # Prefer the longest match so a short city name cannot shadow a longer one.
    for city in sorted(set(candidates), key=len, reverse=True):
        if city.casefold() in message_folded:
            return city
    return None


def current_customer_message_for_preflight(input_data: dict[str, Any]) -> str:
    """Select only the current customer turn for deterministic preflight checks.

    Older and non-widget Runs may not have the dedicated field, so retain the
    legacy message fallback for compatibility. New widget Runs always set it.
    """
    current_message = input_data.get("current_customer_message")
    if isinstance(current_message, str):
        return current_message
    return str(input_data.get("message", ""))


def shipping_fee_preflight_response(message: str, policy: dict[str, Any] | None = None,
                                   known_slots: dict[str, Any] | None = None) -> str | None:
    """Return a safe deterministic reply when a shipping-fee question lacks a usable rate."""
    normalized_message = message.casefold()
    shipping_fee_terms = (
        "هزینه ارسال", "هزینه‌ی ارسال", "هزینه پست", "کرایه ارسال",
        "قیمت ارسال", "ارسال چقدر", "ارسال چند", "هزینه حمل",
    )
    if not any(term in normalized_message for term in shipping_fee_terms):
        return None

    trusted_policy = policy if isinstance(policy, dict) else {}
    shipping = trusted_policy.get("shipping")
    shipping = shipping if isinstance(shipping, dict) else {}
    if has_valid_flat_shipping_rate(shipping):
        return None

    rates_by_city = shipping.get("rates_by_city")
    configured_cities = set(rates_by_city.keys()) if isinstance(rates_by_city, dict) else set()
    configured_list = shipping.get("cities", shipping.get("known_cities", []))
    if isinstance(configured_list, list):
        configured_cities.update(item for item in configured_list if isinstance(item, str))
    current_city_mentions = {
        city_name for city_name in configured_cities
        if isinstance(city_name, str)
        and re.search(rf"(?<![\w]){re.escape(city_name)}(?![\w])", message, re.UNICODE)
    }
    alternative_destinations = re.search(
        r"(?:به|برای)\s+[\w‌-]+\s+یا\s+[\w‌-]+",
        message,
        re.UNICODE,
    )
    if len(current_city_mentions) > 1 or alternative_destinations:
        return plan_support_turn(intent="shipping_fee", policy=trusted_policy).next_question
    explicit_destination = re.search(
        r"(?:به|برای)\s+(?!کدوم\s+شهر|چه\s+شهری|همون\s+شهر|همان\s+شهر|همون\s+مقصد|همان\s+مقصد)([\w‌-]+)",
        message,
        re.UNICODE,
    )
    if explicit_destination and not current_city_mentions:
        return "برای این مقصد نرخ ارسالِ تأییدشده‌ای در اطلاعات فروشگاه ندارم؛ برای اعلام مبلغ دقیق، لازم است پشتیبانی بررسی کند."
    prior_city = (known_slots or {}).get("city") if isinstance(known_slots, dict) else None
    city = prior_city if isinstance(prior_city, str) and prior_city in configured_cities else find_trusted_shipping_city(message, shipping)
    if city is None:
        return plan_support_turn(intent="shipping_fee", policy=trusted_policy).next_question

    decision = plan_support_turn(
        intent="shipping_fee",
        known_slots={"city": city},
        policy=trusted_policy,
    )
    if decision.can_answer_from_policy:
        return None
    return "برای این شهر نرخ ارسالِ تأییدشده‌ای در اطلاعات فروشگاه ندارم؛ برای اعلام مبلغ دقیق، لازم است پشتیبانی بررسی کند."



def support_slot_preflight_response(
    message: str,
    policy: dict[str, Any] | None = None,
    known_slots: dict[str, Any] | None = None,
) -> str | None:
    """Ask the first missing required slot before invoking the model.

    This is intentionally limited to explicit, unambiguous intent phrases.
    It never synthesizes a business answer; complete requests continue through
    the normal policy-guarded model/tool path.
    """
    intent = detect_support_intent(message)
    if intent is None:
        return None
    if intent == "shipping_fee":
        return shipping_fee_preflight_response(message, policy, known_slots)
    decision = plan_support_turn(
        intent=intent,
        known_slots=known_slots,
        policy=policy,
    )
    return decision.next_question if decision.missing_slots else None
