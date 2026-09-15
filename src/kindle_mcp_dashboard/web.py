from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .renderer import render_png
from .store import DashboardStore


def serve(host: str = "0.0.0.0", port: int = 8787, refresh: int = 60) -> None:
    store = DashboardStore()
    store.ensure()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path in {"/", "/kindle"}:
                body = _page(refresh).encode()
                self._send(HTTPStatus.OK, "text/html; charset=utf-8", body)
            elif path == "/screen.png":
                self._send(HTTPStatus.OK, "image/png", render_png(store.read()))
            elif path == "/api/state":
                self._send(HTTPStatus.OK, "application/json", json.dumps(store.read()).encode())
            elif path == "/health":
                self._send(HTTPStatus.OK, "application/json", b'{"status":"ok"}')
            else:
                self._send(HTTPStatus.NOT_FOUND, "text/plain", b"Not found\n")

        def _send(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: object) -> None:
            print(f"kindle {self.client_address[0]}: {fmt % args}")

    print(f"Kindle dashboard: http://{host}:{port}/kindle")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


def _page(refresh: int) -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="{max(10, refresh)}">
<title>Kindle Dashboard</title>
<style>html,body{{margin:0;padding:0;background:#fff;width:100%;height:100%;overflow:hidden}}img{{display:block;width:100%;height:100%;object-fit:contain}}</style>
</head><body><img src="/screen.png" alt="Dashboard"></body></html>"""

