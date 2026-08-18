#!/usr/bin/env python3
"""Real-stack Product Acceptance gate for Orders/Sales/Invoice/Billing."""
import os
import requests

BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
TOKEN = os.getenv("CERT_TOKEN")
TENANT = os.getenv("CERT_TENANT_ID")
if not TOKEN or not TENANT:
    raise SystemExit("CERT_TOKEN and CERT_TENANT_ID are required")
S = requests.Session()
S.headers.update({"Authorization": f"Bearer {TOKEN}", "X-Tenant-ID": TENANT})

def req(method, path, **kwargs):
    r = S.request(method, BASE + path, timeout=30, **kwargs)
    if not r.ok:
        raise AssertionError(f"{method} {path}: {r.status_code} {r.text[:1000]}")
    return r.json() if r.content else None

req("GET", "/api/v1/billing/plans")
order = req("POST", "/api/v1/orders", json={"customer_name": "PA Gate Customer", "items": []})
order_id = order.get("id"); assert order_id, order
invoice = req("POST", "/api/v1/invoices", json={"order_id": order_id, "amount": "100.00"})
invoice_id = invoice.get("id"); assert invoice_id, invoice
sale = req("POST", "/api/v1/sales", json={"order_id": order_id, "amount": "100.00"})
sale_id = sale.get("id"); assert sale_id, sale
for resource, rid, statuses in (("orders", order_id, ("confirmed", "completed")), ("sales", sale_id, ("won",)), ("invoices", invoice_id, ("issued", "paid"))):
    for status in statuses:
        r = S.patch(f"{BASE}/api/v1/{resource}/{rid}", json={"status": status}, timeout=30)
        if r.status_code in (200, 204): break
        if r.status_code not in (400, 409, 422):
            raise AssertionError(f"PATCH {resource}/{rid}: {r.status_code} {r.text[:500]}")
for resource, rid in (("orders", order_id), ("sales", sale_id), ("invoices", invoice_id)):
    req("GET", f"/api/v1/{resource}/{rid}")
print("ORDERS_SALES_INVOICE_BILLING_REAL_STACK_PASS")
