from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse

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
                # Calculate path to index.html relative to this file (api/main.py)
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
                pass # Fall through to default behavior

        # 2. Handle API calls
        if path.startswith("/api"):
            # Only check password for API calls
            if auth_header == app_password:
                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                
                if path == "/api/verify" or path == "/api/v1/health":
                    body = json.dumps({"status": "ok", "authenticated": True}).encode()
                else:
                    self.send_response(404)
                    body = json.dumps({"error": "Endpoint not found", "path": path}).encode()
            else:
                self.send_response(401)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                body = json.dumps({"error": "Unauthorized", "authenticated": False}).encode()

            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            # 404 for unknown non-API paths
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def log_message(self, *args):
        pass
