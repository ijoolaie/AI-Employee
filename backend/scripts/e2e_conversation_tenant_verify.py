"""Real-stack certification for authenticated/public conversation tenant boundaries."""
from __future__ import annotations

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.getenv("E2E_API_BASE_URL", "http://localhost:8000/api/v1")
PASSWORD = "ConversationTenant-P0-2026!"


def request(method: str, path: str, payload: dict | None = None, token: str | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode()
    h = {"Accept": "application/json", "Content-Type": "application/json"}
    if headers: h.update(headers)
    if token: h["Authorization"] = f"Bearer {token}"
    req = Request(f"{BASE_URL}{path}", data=body, headers=h, method=method)
    try:
        with urlopen(req, timeout=15) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode()
        try: return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError: return exc.code, {"raw": raw}
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def assert_status(actual: int, expected: int | tuple[int, ...], label: str, body: dict) -> None:
    allowed = expected if isinstance(expected, tuple) else (expected,)
    assert actual in allowed, f"{label}: expected {allowed}, got {actual}: {body}"


def register(suffix: str, label: str) -> tuple[str, str]:
    slug = f"conv-cert-{label}-{suffix}"
    email = f"i.joolaie+conv-cert-{label}-{suffix}@gmail.com"
    status, body = request("POST", "/auth/register", {"tenant_name": f"Conversation {label} {suffix}", "tenant_slug": slug, "email": email, "password": PASSWORD, "full_name": f"Conversation {label} Admin"})
    assert_status(status, 201, f"{label} registration", body)
    token = (body.get("data") or {}).get("access_token")
    assert token, body
    return slug, token


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    tenant_a, token_a = register(suffix, "a")
    tenant_b, token_b = register(suffix, "b")
    print(f"TENANT A REGISTER PASS tenant={tenant_a}")
    print(f"TENANT B REGISTER PASS tenant={tenant_b}")

    status, employee = request("POST", "/employees", {"slug": f"conv-cert-employee-{suffix}", "name": "Conversation Certification Employee", "kind": "custom", "input_schema": {}, "output_schema": {}, "prompt_template": "Return the input unchanged.", "allowed_tools": [], "rules": {}}, token=token_a)
    assert_status(status, 201, "tenant A employee", employee)
    employee_id = (employee.get("data") or {}).get("id")
    assert employee_id
    status, channel = request("POST", "/customer-channels", {"employee_id": employee_id, "name": "Conversation Certification Widget", "channel_type": "web_widget", "config": {}}, token=token_a)
    assert_status(status, 201, "tenant A channel", channel)
    public_key = (channel.get("data") or {}).get("public_key")
    assert public_key
    status, created = request("POST", f"/public/chat/channels/{public_key}/conversations", {"customer_name": "Tenant A Customer", "customer_email": f"a-{suffix}@example.com"})
    assert_status(status, 200, "public conversation create", created)
    data = created.get("data") or {}
    conversation_id = data.get("id")
    customer_token_a = data.get("customer_token")
    assert conversation_id and customer_token_a
    print(f"TENANT A PUBLIC CONVERSATION CREATE PASS conversation={conversation_id}")

    status, own = request("GET", f"/public/chat/conversations/{conversation_id}", headers={"X-Customer-Token": customer_token_a})
    assert_status(status, 200, "same-customer public read", own)
    print("SAME-CONVERSATION PUBLIC READ PASS")

    status, list_b = request("GET", "/customer-channels/conversations", token=token_b)
    assert_status(status, 200, "tenant B conversation list", list_b)
    assert not any(item.get("id") == conversation_id for item in (list_b.get("data") or []))
    print("CROSS-TENANT AUTHENTICATED CONVERSATION LIST ISOLATION PASS")

    status, wrong = request("GET", f"/public/chat/conversations/{conversation_id}", headers={"X-Customer-Token": "not-the-owner-token"})
    assert_status(status, 404, "wrong customer token", wrong)
    print("WRONG CUSTOMER TOKEN REJECT PASS")

    # Tenant B creates its own channel/conversation. Its customer token must not
    # grant access to Tenant A's conversation, proving a real two-tenant boundary.
    status, employee_b = request("POST", "/employees", {"slug": f"conv-cert-employee-b-{suffix}", "name": "Conversation B Employee", "kind": "custom", "input_schema": {}, "output_schema": {}, "prompt_template": "Return the input unchanged.", "allowed_tools": [], "rules": {}}, token=token_b)
    assert_status(status, 201, "tenant B employee", employee_b)
    employee_b_id = (employee_b.get("data") or {}).get("id")
    status, channel_b = request("POST", "/customer-channels", {"employee_id": employee_b_id, "name": "Conversation B Widget", "channel_type": "web_widget", "config": {}}, token=token_b)
    assert_status(status, 201, "tenant B channel", channel_b)
    public_key_b = (channel_b.get("data") or {}).get("public_key")
    status, conv_b = request("POST", f"/public/chat/channels/{public_key_b}/conversations", {"customer_name": "Tenant B Customer", "customer_email": f"b-{suffix}@example.com"})
    assert_status(status, 200, "tenant B public conversation", conv_b)
    customer_token_b = (conv_b.get("data") or {}).get("customer_token")
    assert customer_token_b
    status, cross_read = request("GET", f"/public/chat/conversations/{conversation_id}", headers={"X-Customer-Token": customer_token_b})
    assert_status(status, 404, "tenant B customer token reading tenant A", cross_read)
    print("CROSS-TENANT PUBLIC CONVERSATION READ REJECT PASS")

    status, cross_handoff = request("POST", f"/conversations/{conversation_id}/handoff", {"requested": True, "assigned_user_id": None}, token=token_b)
    assert_status(status, (403, 404), "cross-tenant conversation handoff", cross_handoff)
    print("CROSS-TENANT HANDOFF REJECT PASS")

    print("CONVERSATION TENANT ISOLATION P0 REAL-STACK CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
