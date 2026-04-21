"""
/api/v1/health.py
Simple health check — returns API info and available endpoints (v1).
"""

from http.server import BaseHTTPRequestHandler
import json
from lib.auth import check_auth


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if not check_auth(self):
            return
        data = {
            "status": "ok",
            "version": "1.0.0",
            "api_version": "v1",
            "endpoints": {
                "/api/v1/analyze": {
                    "methods": ["GET", "POST"],
                    "description": "Full axe-core WCAG audit",
                    "accepts_post": {"url": "string (optional)", "html": "string (optional)"},
                    "accepts_get": {"url": "string"},
                    "returns": "violations, passes, incomplete + score 0-100"
                },
                "/api/v1/lighthouse": {
                    "methods": ["GET", "POST"],
                    "description": "Lighthouse-style multi-category audit (URL only)",
                    "accepts": {"url": "string"},
                    "returns": "performance, accessibility, best-practices, SEO scores"
                },
                "/api/v1/health": {
                    "methods": ["GET"],
                    "description": "API status and documentation"
                }
            },
            "engines": ["axe-core 4.9.1", "Playwright Chromium", "custom Lighthouse-style heuristics"]
        }
        body = json.dumps(data, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass
