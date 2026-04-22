from http.server import BaseHTTPRequestHandler
import json
import sys
import os

v1_path = os.path.join(os.path.dirname(__file__), "v1")
lib_path = os.path.join(v1_path, "lib")
sys.path.insert(0, v1_path)
sys.path.insert(0, lib_path)

from health import handler as health_handler
from analyze import handler as analyze_handler
from lighthouse import handler as lighthouse_handler
from urllib.parse import urlparse

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self._route()

    def do_GET(self):
        self._route()

    def do_POST(self):
        self._route()

    def _route(self):
        path = urlparse(self.path).path.rstrip("/")

        if path == "/api/v1/health":
            h = health_handler(self.request, self.client_address, self.server)
            h.handle()
        elif path == "/api/v1/analyze":
            h = analyze_handler(self.request, self.client_address, self.server)
            h.handle()
        elif path == "/api/v1/lighthouse":
            h = lighthouse_handler(self.request, self.client_address, self.server)
            h.handle()
        else:
            body = json.dumps({"error": "Not found", "path": path}).encode()
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, *args):
        pass