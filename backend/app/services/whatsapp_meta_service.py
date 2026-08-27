"""Small, fail-closed adapter for Meta WhatsApp Cloud API."""
from __future__ import annotations

import hashlib
import hmac
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def verify_webhook_signature(raw_body: bytes, signature: str | None, app_secret: str | None) -> bool:
    if not raw_body or not signature or not app_secret:
        return False
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature[7:], expected)


def verify_webhook_challenge(mode: str | None, token: str | None, challenge: str | None, expected_token: str | None) -> str | None:
    if mode != "subscribe" or not challenge or not expected_token:
        return None
    if not token or not hmac.compare_digest(token, expected_token):
        return None
    return challenge


def extract_text_messages(payload: dict) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                sender = message.get("from")
                text = ((message.get("text") or {}).get("body") or "").strip()
                message_id = message.get("id")
                if sender and text:
                    messages.append({"from_phone": sender, "text": text, "message_id": message_id or ""})
    return messages


def send_text_message(*, access_token: str | None, phone_number_id: str | None, to_phone: str, text: str, graph_api_version: str = "v23.0") -> dict:
    if not access_token or not phone_number_id:
        raise RuntimeError("WhatsApp provider credentials are not configured")
    if not to_phone or not text:
        raise ValueError("WhatsApp recipient and text are required")
    url = f"https://graph.facebook.com/{graph_api_version}/{phone_number_id}/messages"
    payload = json.dumps({"messaging_product": "whatsapp", "to": to_phone, "type": "text", "text": {"body": text}}).encode()
    req = Request(url, data=payload, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else {}
    except (HTTPError, URLError) as exc:
        raise RuntimeError("WhatsApp provider request failed") from exc
