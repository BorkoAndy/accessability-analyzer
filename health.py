"""
/api/health.py
Simple health check — returns API info and available endpoints.
"""

from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        data = {
            "status": "ok",
            "version": "1.0.0",
            "endpoints": {
                "POST /api/analyze": {
                    "description": "Full axe-core WCAG audit",
                    "accepts": {"url": "string (optional)", "html": "string (optional)"},
                    "returns": "violations, passes, incomplete + score 0-100"
                },
                "POST /api/lighthouse": {
                    "description": "Lighthouse-style multi-category audit (URL only)",
                    "accepts": {"url": "string"},
                    "returns": "performance, accessibility, best-practices, SEO scores"
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
