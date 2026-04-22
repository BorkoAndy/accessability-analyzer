from http.server import BaseHTTPRequestHandler
import json
import sys
import os

v1_path = os.path.join(os.path.dirname(__file__), "v1")
lib_path = os.path.join(v1_path, "lib")
sys.path.insert(0, v1_path)
sys.path.insert(0, lib_path)

import health
import analyze
import lighthouse
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
            health.handler.do_GET(self)
        elif path == "/api/v1/analyze":
            if self.command == "POST":
                analyze.handler.do_POST(self)
            else:
                analyze.handler.do_GET(self)
        elif path == "/api/v1/lighthouse":
            if self.command == "POST":
                lighthouse.handler.do_POST(self)
            else:
                lighthouse.handler.do_GET(self)
        else:
            body = json.dumps({"error": "Not found", "path": path}).encode()
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, *args):
        pass