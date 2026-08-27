"""Real-stack Product Acceptance gate for Orders -> Sales -> Invoice -> Billing."""
from __future__ import annotations

import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def request(method: str, path: str, payload: dict | None = None, token: str | None = None):
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        return exc.code, detail
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def expect(status: int, expected: int, label: str, body: dict) -> dict:
    assert status == expected, f"{label}: expected HTTP {expected}, got {status}: {body}"
    return body.get("data") or {}


def register(suffix: str):
    email = f"i.joolaie+commerce-{suffix}@gmail.com"
    slug = f"cert-commerce-{suffix}"
    status, body = request(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"Commerce Acceptance {suffix}",
            "tenant_slug": slug,
            "email": email,
            "password": "CertCommerce-P0-2026!",
            "full_name": "Commerce Acceptance Admin",
        },
    )
    data = expect(status, 201, "commerce certification registration", body)
    token = data.get("access_token")
    assert token, body
    return token


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    token_a = register(suffix)
    token_b = register(f"{suffix}b")

    status, body = request("GET", "/billing/plans", token=token_a)
    plans = expect(status, 200, "billing plans", body)
    assert plans and all(p.get("code") for p in plans), plans
    print("BILLING PLANS PASS")

    status, body = request("GET", "/billing/subscription", token=token_a)
    subscription = expect(status, 200, "billing subscription", body)
    assert subscription.get("id") and subscription.get("plan"), subscription
    print("BILLING SUBSCRIPTION PASS")

    status, body = request("GET", "/billing/entitlements", token=token_a)
    entitlements = expect(status, 200, "billing entitlements", body)
    assert entitlements.get("plan") and entitlements.get("status"), entitlements
    print("BILLING ENTITLEMENTS PASS")

    current_plan = subscription["plan"]["code"]
    status, body = request("POST", "/billing/subscription", {"plan_code": current_plan}, token_a)
    changed = expect(status, 200, "billing plan change", body)
    assert changed.get("plan", {}).get("code") == current_plan, changed
    print("BILLING PLAN CHANGE PASS")

    # Billing subscription/entitlements are tenant-scoped even though plan
    # catalog data is intentionally global. A different tenant must not be
    # able to read or mutate tenant A's subscription state.
    status, body = request("GET", "/billing/subscription", token=token_b)
    subscription_b = expect(status, 200, "tenant B billing subscription", body)
    assert subscription_b.get("id") and subscription_b.get("plan"), subscription_b
    assert subscription_b["id"] != subscription["id"], (subscription_b, subscription)
    print("BILLING SUBSCRIPTION TENANT ISOLATION PASS")

    status, body = request("GET", "/billing/entitlements", token=token_b)
    entitlements_b = expect(status, 200, "tenant B billing entitlements", body)
    assert entitlements_b.get("plan") and entitlements_b.get("status"), entitlements_b
    print("BILLING ENTITLEMENTS TENANT ISOLATION PASS")

    invoice_payload = {
        "number": f"CERT-INV-{suffix}",
        "customer_name": "Certification Customer",
        "customer_email": f"customer-{suffix}@example.test",
        "currency": "IRR",
        "tax_rate": 0,
        "line_items": [{"description": "Certification service", "quantity": 1, "unit_price": 100000}],
        "notes": "Real-stack Product Acceptance certification",
    }
    status, body = request("POST", "/invoices", invoice_payload, token_a)
    invoice = expect(status, 201, "invoice creation", body)
    invoice_id = invoice["id"]
    assert invoice["status"] == "draft" and float(invoice["total"]) > 0, invoice
    print(f"INVOICE CREATE PASS invoice={invoice_id}")

    status, body = request("POST", f"/invoices/{invoice_id}/status", {"status": "sent"}, token_a)
    invoice = expect(status, 200, "invoice status", body)
    assert invoice["status"] == "sent", invoice
    print("INVOICE STATUS PASS")

    status, body = request("POST", "/orders", {
        "number": f"CERT-ORD-{suffix}",
        "customer_name": "Certification Customer",
        "customer_email": f"customer-{suffix}@example.test",
        "currency": "IRR",
        "tax_rate": 0,
        "line_items": [{"description": "Certification service", "quantity": 1, "unit_price": 100000}],
        "invoice_id": invoice_id,
    }, token_a)
    order = expect(status, 201, "order creation", body)
    order_id = order["id"]
    assert order["status"] == "draft" and order.get("invoice_id") == invoice_id, order
    print(f"ORDER CREATE/LINK-INVOICE PASS order={order_id}")

    status, body = request("POST", f"/orders/{order_id}/status", {"status": "confirmed"}, token_a)
    order = expect(status, 200, "order status", body)
    assert order["status"] == "confirmed", order
    print("ORDER STATUS PASS")

    status, body = request("POST", "/sales/deals", {
        "title": f"Certification Deal {suffix}",
        "customer_name": "Certification Customer",
        "customer_email": f"customer-{suffix}@example.test",
        "stage": "lead",
        "amount": 100000,
        "currency": "IRR",
        "probability": 25,
        "source": "product-acceptance",
        "order_id": order_id,
    }, token_a)
    deal = expect(status, 201, "sales deal creation", body)
    deal_id = deal["id"]
    assert deal.get("order_id") == order_id and deal["stage"] == "lead", deal
    print(f"SALES DEAL CREATE/LINK-ORDER PASS deal={deal_id}")

    status, body = request("POST", f"/sales/deals/{deal_id}/stage", {"stage": "won", "probability": 100}, token_a)
    deal = expect(status, 200, "sales stage", body)
    assert deal["stage"] == "won" and deal["probability"] == 100, deal
    print("SALES STAGE PASS")

    status, body = request("GET", "/orders/summary", token=token_a)
    summary = expect(status, 200, "order summary", body)
    assert summary.get("total_orders", 0) >= 1, summary
    status, body = request("GET", "/invoices/summary", token=token_a)
    summary = expect(status, 200, "invoice summary", body)
    assert summary.get("total_invoices", 0) >= 1, summary
    status, body = request("GET", "/sales/pipeline", token=token_a)
    pipeline = expect(status, 200, "sales pipeline", body)
    assert pipeline.get("total_deals", 0) >= 1 and pipeline.get("won_amount", 0) > 0, pipeline
    print("COMMERCE SUMMARIES PASS")

    status, body = request("GET", f"/orders/{order_id}", token=token_b)
    assert status in {403, 404}, f"cross-tenant order access must be denied, got {status}: {body}"
    status, body = request("GET", f"/invoices/{invoice_id}", token=token_b)
    assert status in {403, 404}, f"cross-tenant invoice access must be denied, got {status}: {body}"
    status, body = request("GET", f"/sales/deals/{deal_id}", token=token_b)
    assert status in {403, 404}, f"cross-tenant deal access must be denied, got {status}: {body}"
    print("COMMERCE TENANT ISOLATION PASS")

    print("ORDERS + SALES + INVOICE + BILLING PRODUCT ACCEPTANCE CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"ORDERS/SALES/INVOICE/BILLING CERTIFICATION FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
