from __future__ import annotations

from typing import Dict, Any
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from .kernel import Kernel


class KernelHandler(BaseHTTPRequestHandler):
    kernel = Kernel()

    def do_POST(self):  # noqa: N802
        if self.path != "/handle":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
            cmd = payload.get("command", "")
            ctx = payload.get("context", {})
            resp = self.kernel.handle(cmd, ctx)
            self._json(resp)
        except Exception as e:
            self._json({"status": "error", "result": str(e)})

    def _json(self, obj: Dict[str, Any]) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    httpd = HTTPServer((host, port), KernelHandler)
    httpd.serve_forever()
