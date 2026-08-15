"""Verify the configured LM Studio OpenAI-compatible endpoint.

Usage:
    python scripts/verify_lm_studio.py

This checks /v1/models and then performs one short /v1/chat/completions call.
It is intentionally independent of the database/Celery stack.
"""

import os
import sys

import httpx

BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
MODEL = os.getenv("AI_DEFAULT_MODEL", "google/gemma-4-e4b")
API_KEY = os.getenv("LM_STUDIO_API_KEY", "")

headers = {"content-type": "application/json"}
if API_KEY:
    headers["authorization"] = f"Bearer {API_KEY}"

try:
    with httpx.Client(timeout=30.0) as client:
        models = client.get(f"{BASE_URL}/models", headers=headers)
        models.raise_for_status()
        model_ids = [m.get("id") for m in models.json().get("data", [])]
        print("LM Studio reachable:", BASE_URL)
        print("Available models:", model_ids)
        if MODEL not in model_ids:
            print(f"WARNING: configured model '{MODEL}' was not reported by /models.")

        response = client.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "user", "content": "Reply with exactly: LM Studio OK"}
                ],
                "max_tokens": 32,
                "temperature": 0,
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        print("Model response:", content)
        print("LM Studio smoke test: PASS")
except Exception as exc:
    print("LM Studio smoke test: FAIL")
    print(type(exc).__name__ + ":", exc)
    sys.exit(1)
