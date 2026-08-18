"""Real-stack Product Acceptance certification for Files -> Knowledge -> Memory."""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def request(method: str, path: str, payload: dict | None = None, token: str | None = None, body: bytes | None = None, content_type: str = "application/json") -> tuple[int, dict | bytes]:
    data = body if body is not None else (None if payload is None else json.dumps(payload).encode())
    headers = {"Accept": "application/json", "Content-Type": content_type}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read()
            if response.headers.get_content_type() == "application/json":
                return response.status, json.loads(raw.decode())
            return response.status, raw
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        raise AssertionError(f"{method} {path} returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def upload_text(filename: str, content: str, token: str) -> tuple[int, dict]:
    boundary = f"----Certification{uuid.uuid4().hex}"
    payload = content.encode()
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: text/plain\r\n\r\n".encode(),
        payload,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    status, result = request("POST", "/files", token=token, body=b"".join(parts), content_type=f"multipart/form-data; boundary={boundary}")
    assert isinstance(result, dict)
    return status, result


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    tenant_slug = f"cert-files-km-{suffix}"
    email = "i.joolaie@gmail.com"
    password = "CertFilesKM-2026!"

    status, registered = request("POST", "/auth/register", {
        "tenant_name": f"Files Knowledge Memory {suffix}",
        "tenant_slug": tenant_slug,
        "email": email,
        "password": password,
        "full_name": "Files Knowledge Memory User",
    })
    assert status == 201, f"registration expected 201, got {status}: {registered}"
    token = (registered.get("data") or {}).get("access_token")
    assert token, registered
    print("FILES/KM AUTH PASS")

    employee_payload = {
        "slug": f"cert-km-employee-{suffix}",
        "name": "Knowledge Memory Employee",
        "kind": "custom",
        "input_schema": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]},
        "output_schema": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}},
        "prompt_template": "Complete: {{task}}",
        "allowed_tools": [],
        "rules": {},
    }
    status, created = request("POST", "/employees", employee_payload, token)
    assert status == 201, created
    employee_id = (created.get("data") or {}).get("id")
    assert employee_id, created

    knowledge_text = "Acme certification knowledge: the approved support window is Monday through Friday at 09:00 UTC."
    status, uploaded = upload_text(f"cert-knowledge-{suffix}.txt", knowledge_text, token)
    assert status == 201, uploaded
    file_id = (uploaded.get("data") or {}).get("id")
    assert file_id, uploaded
    print("FILES UPLOAD PASS")

    status, listed = request("GET", "/files", token=token)
    assert status == 200, listed
    assert any(item.get("id") == file_id for item in (listed.get("data") or [])), listed

    status, metadata = request("GET", f"/files/{file_id}", token=token)
    assert status == 200, metadata
    assert (metadata.get("data") or {}).get("filename") == f"cert-knowledge-{suffix}.txt", metadata

    status, downloaded = request("GET", f"/files/{file_id}/download", token=token)
    assert status == 200 and isinstance(downloaded, bytes), "file download failed"
    assert downloaded.decode() == knowledge_text, "downloaded file content mismatch"
    print("FILES LIST/GET/DOWNLOAD PASS")

    status, indexed = request("POST", "/knowledge/index", {"file_id": file_id}, token)
    assert status == 201, indexed
    document = indexed.get("data") or {}
    assert document.get("status") == "indexed", indexed
    assert document.get("chunk_count", 0) >= 1, indexed
    print("KNOWLEDGE INDEX PASS")

    status, searched = request("POST", "/knowledge/search", {"query": "approved support window Monday Friday", "top_k": 5}, token)
    assert status == 200, searched
    results = searched.get("data") or []
    assert results and any(file_id == item.get("file_id") and "approved support window" in item.get("content", "") for item in results), searched
    print("KNOWLEDGE SEARCH PASS")

    memory_content = "The customer prefers the approved support window Monday through Friday at 09:00 UTC."
    status, memory_created = request("POST", "/memory", {
        "employee_id": employee_id,
        "content": memory_content,
        "memory_type": "preference",
        "importance": 4,
        "metadata": {"certification": True},
    }, token)
    assert status == 201, memory_created
    memory = memory_created.get("data") or {}
    memory_id = memory.get("id")
    assert memory_id and memory.get("version") == 1 and memory.get("status") == "active", memory_created
    print("MEMORY CREATE PASS")

    status, memory_search = request("POST", "/memory/search", {
        "employee_id": employee_id,
        "query": "customer prefers approved support window Monday Friday",
        "top_k": 5,
        "min_score": 0.35,
    }, token)
    assert status == 200, memory_search
    memories = memory_search.get("data") or []
    assert any(item.get("id") == memory_id and item.get("status") == "active" for item in memories), memory_search
    print("MEMORY SEARCH PASS")
    print("PRODUCT ACCEPTANCE FILES -> KNOWLEDGE -> MEMORY PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"PRODUCT ACCEPTANCE FILES/KNOWLEDGE/MEMORY FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
