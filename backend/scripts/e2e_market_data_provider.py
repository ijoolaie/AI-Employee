"""E2E-only deterministic market-data provider."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class Handler(BaseHTTPRequestHandler):
    def _write(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _market_response(self, path, symbols, horizon):
        if path == "/v1/market/research":
            return {
                "provider": "e2e-deterministic",
                "as_of": "2026-01-01T00:00:00Z",
                "symbols": symbols,
                "horizon_days": horizon,
                "results": [
                    {"symbol": s, "signal": "neutral", "confidence": 0.5}
                    for s in symbols
                ],
            }

        if path == "/v1/market/risk-analysis":
            return {
                "provider": "e2e-deterministic",
                "as_of": "2026-01-01T00:00:00Z",
                "symbols": symbols,
                "horizon_days": horizon,
                "results": [
                    {"symbol": s, "risk": "moderate", "score": 0.5}
                    for s in symbols
                ],
            }

        if path == "/v1/market/trading-plan":
            return {
                "provider": "e2e-deterministic",
                "as_of": "2026-01-01T00:00:00Z",
                "symbols": symbols,
                "horizon_days": horizon,
                "plan": {
                    "objective": "balanced",
                    "mode": "paper_review",
                    "execution": "human_approval_required",
                },
            }

        return None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            self._write(200, {"status": "ok", "provider": "e2e-deterministic"})
            return

        if path in {
            "/v1/market/research",
            "/v1/market/risk-analysis",
            "/v1/market/trading-plan",
        }:
            query = parse_qs(parsed.query)
            symbols = [
                s.strip()
                for s in (query.get("symbols", ["AAPL"])[0]).split(",")
                if s.strip()
            ]
            horizon = int(query.get("horizon_days", ["30"])[0])

            payload = self._market_response(path, symbols, horizon)
            self._write(200, payload)
            return

        self._write(404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        symbols = payload.get("symbols") or ["AAPL"]
        horizon = int(payload.get("horizon_days") or 30)

        response = self._market_response(path, symbols, horizon)
        if response is not None:
            if path == "/v1/market/trading-plan":
                response["plan"]["objective"] = payload.get("objective", "balanced")
            self._write(200, response)
            return

        self._write(404, {"error": "not_found"})

    def log_message(self, *_args):
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8090), Handler).serve_forever()
