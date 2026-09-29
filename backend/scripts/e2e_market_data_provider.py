"""E2E-only deterministic market-data provider.

This service exists only for the Docker certification stack. It returns a
stable read-only response for the governed Workforce market tools and has no
production configuration or credentials.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class Handler(BaseHTTPRequestHandler):
    server_version = "AIEmployeeE2EMarketProvider/1.0"

    def _write(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._write(200, {"status": "ok", "provider": "e2e-deterministic"})
            return
        self._write(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._write(400, {"error": "invalid_json"})
            return

        symbols = payload.get("symbols") or ["AAPL"]
        horizon_days = int(payload.get("horizon_days") or 30)
        path = urlparse(self.path).path

        if path == "/v1/market/research":
            self._write(
                200,
                {
                    "provider": "e2e-deterministic",
                    "as_of": "2026-01-01T00:00:00Z",
                    "symbols": symbols,
                    "horizon_days": horizon_days,
                    "results": [
                        {"symbol": symbol, "signal": "neutral", "confidence": 0.5}
                        for symbol in symbols
                    ],
                },
            )
            return

        if path == "/v1/market/risk-analysis":
            self._write(
                200,
                {
                    "provider": "e2e-deterministic",
                    "as_of": "2026-01-01T00:00:00Z",
                    "symbols": symbols,
                    "horizon_days": horizon_days,
                    "results": [
                        {"symbol": symbol, "risk": "moderate", "score": 0.5}
                        for symbol in symbols
                    ],
                },
            )
            return

        if path == "/v1/market/trading-plan":
            objective = payload.get("objective") or "balanced"
            self._write(
                200,
                {
                    "provider": "e2e-deterministic",
                    "as_of": "2026-01-01T00:00:00Z",
                    "symbols": symbols,
                    "horizon_days": horizon_days,
                    "plan": {
                        "objective": objective,
                        "mode": "paper_review",
                        "execution": "human_approval_required",
                    },
                },
            )
            return

        self._write(404, {"error": "not_found"})

    def log_message(self, _format: str, *_args) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8090), Handler).serve_forever()
