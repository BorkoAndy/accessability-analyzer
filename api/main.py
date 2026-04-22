from http.server import BaseHTTPRequestHandler
import json
import sys
import os

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        v1_path = os.path.join(os.path.dirname(__file__), "v1")
        body = json.dumps({
            "v1_contents": os.listdir(v1_path),
            "lib_contents": os.listdir(os.path.join(v1_path, "lib")) if os.path.exists(os.path.join(v1_path, "lib")) else "no lib folder",
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass