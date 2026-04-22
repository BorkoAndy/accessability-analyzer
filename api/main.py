from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        self.end_headers()

    def do_GET(self):
        self._route()

    def do_POST(self):
        self._route()

    def _route(self):
        path = urlparse(self.path).path.rstrip("/")
        auth_header = self.headers.get("X-API-Key")
        app_password = os.environ.get("APP_PASSWORD", "demo")

        # CORS Headers
        def send_cors_headers():
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")

        # 1. Verification Endpoint (Special case: doesn't require auth header to CHECK the header)
        # Actually, let's just make one logic: if header is correct, you get 200 OK.
        
        if auth_header == app_password:
            self.send_response(200)
            send_cors_headers()
            self.send_header("Content-Type", "application/json")
            
            if path == "/api/verify" or path == "/api/v1/health":
                body = json.dumps({"status": "ok", "authenticated": True}).encode()
            else:
                self.send_response(404)
                body = json.dumps({"error": "Endpoint not found", "path": path}).encode()
        else:
            self.send_response(401)
            send_cors_headers()
            self.send_header("Content-Type", "application/json")
            body = json.dumps({"error": "Unauthorized", "authenticated": False}).encode()

        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass
