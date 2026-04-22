from http.server import BaseHTTPRequestHandler
import json
import sys
import os

v1_path = os.path.join(os.path.dirname(__file__), "v1")
sys.path.insert(0, v1_path)

import_errors = {}

try:
    from health import handler as health_handler
except Exception as e:
    import_errors["health"] = str(e)

try:
    from analyze import handler as analyze_handler
except Exception as e:
    import_errors["analyze"] = str(e)

try:
    from lighthouse import handler as lighthouse_handler
except Exception as e:
    import_errors["lighthouse"] = str(e)

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        body = json.dumps({
            "sys_path": sys.path,
            "import_errors": import_errors,
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass