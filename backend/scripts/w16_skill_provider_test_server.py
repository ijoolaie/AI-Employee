"""Deterministic HTTP Skill Provider fixture for CI real-stack verification."""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 18181
API_KEY = os.environ.get("SKILL_PROVIDER_API_KEY", "ci-w16-skill-provider-key")
STATE_FILE = Path("/tmp/w16-skill-provider-last.json")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            return
        self.send_error(404)

    def do_POST(self):
        if self.path != "/execute":
            self.send_error(404)
            return
        if self.headers.get("Authorization") != f"Bearer {API_KEY}":
            self.send_error(401)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 262144:
                self.send_error(413)
                return
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (TypeError, ValueError, UnicodeDecodeError):
            self.send_error(400)
            return

        if not isinstance(payload, dict):
            self.send_error(400)
            return

        STATE_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        response = {
            "provider_fixture": "w16-ci-skill-provider",
            "accepted": True,
            "request_id": payload.get("request_id"),
            "skill_package_id": payload.get("skill_package_id"),
            "input": payload.get("input"),
        }
        raw = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
