"""Local evaluator preview with an explicit public-file allowlist and no uploads."""
from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from ai_ceo.policy import Action, PolicyDenied, authorize

WEB = Path(__file__).resolve().parent.parent / "web"
CONTENT_TYPES = {"index.html": "text/html; charset=utf-8", "review-notice.html": "text/html; charset=utf-8",
                 "catalog.js": "text/javascript; charset=utf-8", "app.js": "text/javascript; charset=utf-8",
                 "style.css": "text/css; charset=utf-8", "robots.txt": "text/plain; charset=utf-8"}
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"


class PreviewHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass  # No file names, user query strings or routine notifications in logs.

    def respond(self, status: int, body: bytes, content_type: str, *, head: bool = False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def read_route(self, *, head=False):
        try:
            authorize(Action.LOCAL_PRODUCT, data_dir=Path(os.getenv("AI_CEO_DATA_DIR", "./data")))
        except PolicyDenied:
            self.respond(503, b"Preview stopped by policy", "text/plain; charset=utf-8", head=head)
            return
        path = unquote(urlsplit(self.path).path)
        if path == "/healthz":
            self.respond(200, json.dumps({"status": "local_preview", "sales_enabled": False,
                "uploads_enabled": False, "cloud_schedule_verified": False}).encode(), "application/json", head=head)
            return
        name = "index.html" if path == "/" else path.lstrip("/")
        if name not in CONTENT_TYPES or path.startswith("//"):
            self.respond(404, b"Not found", "text/plain; charset=utf-8", head=head)
            return
        self.respond(200, (WEB / name).read_bytes(), CONTENT_TYPES[name], head=head)

    def do_GET(self):
        self.read_route()

    def do_HEAD(self):
        self.read_route(head=True)

    def do_POST(self):
        self.respond(503, b'{"error":"research_only_checkout_and_uploads_disabled"}', "application/json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    with ThreadingHTTPServer(("127.0.0.1", args.port), PreviewHandler) as server:
        print(f"Local evaluator: http://127.0.0.1:{args.port}/ — no sales or cloud worker")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
