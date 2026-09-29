"""E2E-only deterministic market-data provider."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
class Handler(BaseHTTPRequestHandler):
    def _write(self, status, payload):
        body=json.dumps(payload).encode(); self.send_response(status); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path == "/health": self._write(200, {"status":"ok","provider":"e2e-deterministic"}); return
        self._write(404, {"error":"not_found"})
    def do_POST(self):
        length=int(self.headers.get("Content-Length","0")); payload=json.loads(self.rfile.read(length) or b"{}")
        symbols=payload.get("symbols") or ["AAPL"]; horizon=int(payload.get("horizon_days") or 30)
        if self.path == "/v1/market/research":
            self._write(200, {"provider":"e2e-deterministic","as_of":"2026-01-01T00:00:00Z","symbols":symbols,"horizon_days":horizon,"results":[{"symbol":s,"signal":"neutral","confidence":0.5} for s in symbols]}); return
        if self.path == "/v1/market/risk-analysis":
            self._write(200, {"provider":"e2e-deterministic","as_of":"2026-01-01T00:00:00Z","symbols":symbols,"horizon_days":horizon,"results":[{"symbol":s,"risk":"moderate","score":0.5} for s in symbols]}); return
        if self.path == "/v1/market/trading-plan":
            self._write(200, {"provider":"e2e-deterministic","as_of":"2026-01-01T00:00:00Z","symbols":symbols,"horizon_days":horizon,"plan":{"objective":payload.get("objective","balanced"),"mode":"paper_review","execution":"human_approval_required"}}); return
        self._write(404, {"error":"not_found"})
    def log_message(self, *_args): return
if __name__ == "__main__": ThreadingHTTPServer(("0.0.0.0",8090),Handler).serve_forever()
