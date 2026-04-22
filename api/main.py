from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from urllib.parse import urlparse

# Add v1 to path for easy imports
v1_path = os.path.join(os.path.dirname(__file__), "v1")
sys.path.insert(0, v1_path)

import health
import analyze
import lighthouse

class handler(BaseHTTPRequestHandler):

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        self._route()

    def do_POST(self):
        self._route()

    def _route(self):
        path = urlparse(self.path).path.rstrip("/")
        auth_header = self.headers.get("X-API-Key")
        app_password = os.environ.get("APP_PASSWORD", "demo")

        # 1. Fallback: If root hits the function, serve index.html directly
        if path == "" or path == "/index.html":
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                index_file = os.path.join(base_dir, "index.html")
                if os.path.exists(index_file):
                    with open(index_file, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", str(len(content)))
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(content)
                    return
            except Exception:
                pass

        # 2. Handle API calls (Password Protected)
        if path.startswith("/api"):
            if auth_header == app_password:
                # ROUTING
                if path == "/api/verify" or path == "/api/v1/health":
                    health.handler.do_GET(self)
                elif path == "/api/v1/analyze":
                    if self.command == "POST":
                        analyze.handler.do_POST(self)
                    else:
                        self.send_response(405)
                        self.end_headers()
                elif path == "/api/v1/lighthouse":
                    if self.command == "POST":
                        lighthouse.handler.do_POST(self)
                    else:
                        self.send_response(405)
                        self.end_headers()
                else:
                    self.send_response(404)
                    self._send_cors_headers()
                    self.send_header("Content-Type", "application/json")
                    body = json.dumps({"error": "Endpoint not found", "path": path}).encode()
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
            else:
                self.send_response(401)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                body = json.dumps({"error": "Unauthorized"}).encode()
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def log_message(self, *args):
        pass
