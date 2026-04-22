import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "v1"))

from analyze import handler as analyze_handler
from health import handler as health_handler
from lighthouse import handler as lighthouse_handler

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self._route()

    def do_GET(self):
        self._route()

    def do_POST(self):
        self._route()

    def _route(self):
        path = urlparse(self.path).path.rstrip("/")

        if path.endswith("/analyze"):
            analyze_handler(self.request, self.client_address, self.server).handle()
        elif path.endswith("/lighthouse"):
            lighthouse_handler(self.request, self.client_address, self.server).handle()
        elif path.endswith("/health"):
            health_handler(self.request, self.client_address, self.server).handle()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def log_message(self, *args):
        pass