"""Loopback browser output. HTTP threads serve immutable game presentations."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Lock, Thread
import time
from urllib.parse import urlsplit

from pixel_ops.core.browser_view import BrowserView


class BrowserOutputServer:
    def __init__(self, pages: dict[str, Path], port=8767, assets=None):
        self.pages = pages
        self.port = int(port)
        self.assets = assets or {}
        self._views: dict[str, BrowserView] = {}
        self._published_at = 0.0
        self._lock = Lock()
        self._server = self._thread = None

    def publish(self, views):
        with self._lock:
            self._views = dict(views)
            self._published_at = time.monotonic()

    def start(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                super().setup()
                self.connection.settimeout(3)

            def do_GET(self):  # noqa: N802
                allowed = {f"127.0.0.1:{owner.port}", f"localhost:{owner.port}"}
                if (self.headers.get("Host", "") not in allowed
                        or self.headers.get("Sec-Fetch-Site") == "cross-site"
                        or self.headers.get("Origin", f"http://127.0.0.1:{owner.port}") not in {f"http://{host}" for host in allowed}):
                    self.send_bytes(403, b"Local requests only", "text/plain")
                    return
                path = urlsplit(self.path).path
                if path == "/health":
                    self.send_bytes(200, b'{"available":true}', "application/json")
                    return
                if path in owner.assets:
                    self.send_bytes(200, owner.assets[path].read_bytes(), "font/ttf")
                    return
                parts = path.strip("/").split("/")
                if parts[0] not in owner.pages or len(parts) > 2:
                    self.send_bytes(404, b"Not found", "text/plain")
                    return
                page = parts[0]
                resource = parts[1] if len(parts) == 2 else "index.html"
                if resource in ("state", "frame.png"):
                    with owner._lock:
                        view = owner._views.get(page) if time.monotonic() - owner._published_at <= 5 else None
                    if resource == "state":
                        body = view.state_json if view else json.dumps({"mode": "thermal", "available": False}).encode()
                        self.send_bytes(200, body, "application/json")
                    else:
                        self.send_bytes(200 if view and view.image_png else 404, view.image_png if view and view.image_png else b"", "image/png")
                    return
                types = {"index.html": "text/html", "app.mjs": "text/javascript", "model.mjs": "text/javascript", "style.css": "text/css"}
                if resource not in types:
                    self.send_bytes(404, b"Not found", "text/plain")
                    return
                self.send_bytes(200, (owner.pages[page] / resource).read_bytes(), types[resource])

            def do_POST(self):  # noqa: N802
                self.send_bytes(405, b"Read-only display", "text/plain")

            def send_bytes(self, status, body, content_type):
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (OSError, TimeoutError):
                    pass

            def log_message(self, *args):
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        self._server.daemon_threads = True
        self.port = self._server.server_port
        self._thread = Thread(target=lambda: self._server.serve_forever(poll_interval=0.1), daemon=True, name="pixel-ops-browser-output")
        self._thread.start()

    def close(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
        if self._thread:
            self._thread.join(timeout=2)
