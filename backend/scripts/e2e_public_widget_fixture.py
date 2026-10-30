"""CI fixture for the public widget."""
import json, os, time, uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = os.getenv("E2E_API_BASE_URL", "http://localhost:8000/api/v1")

def call(method, path, data=None, token=None):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(BASE + path, data=None if data is None else json.dumps(data).encode(), headers=headers, method=method)
    try:
        with urlopen(req, timeout=15) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode()
        try: return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError: return exc.code, {"raw": raw}

def main():
    suffix = uuid.uuid4().hex[:16]
    status, result = call("POST", "/auth/register", {
        "tenant_name": "Widget CI " + suffix, "tenant_slug": "widget-ci-" + suffix,
        "email": "widget-ci-" + suffix + "@example.invalid",
        "password": os.environ.get("CI_FIXTURE_PASSWORD", "ci-only-fixture-password-2026"),
        "full_name": "Widget CI Admin",
    })
    assert status == 201, result
    token = result["data"]["access_token"]
    status, employee = call("POST", "/employees", {
        "slug": "widget-ci-" + suffix, "name": "CI Public Support Employee",
        "kind": "custom", "input_schema": {}, "output_schema": {},
        "prompt_template": "Return the input unchanged.", "allowed_tools": [], "rules": {},
    }, token)
    assert status == 201, employee
    employee_id = employee["data"]["id"]
    for _ in range(10):
        status, _ = call("GET", "/employees/" + employee_id, token=token)
        if status == 200: break
        time.sleep(0.25)
    assert status == 200, "employee did not become visible"
    status, channel = call("POST", "/customer-channels", {
        "employee_id": employee_id, "name": "CI Public Widget",
        "channel_type": "web_widget", "config": {},
    }, token)
    assert status == 201, channel
    key = channel["data"]["public_key"]
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as stream:
        stream.write("PUBLIC_CHAT_KEY=" + key + "\n")
    print("Disposable public widget fixture provisioned.")

if __name__ == "__main__":
    main()
