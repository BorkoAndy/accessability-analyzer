from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import traceback

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            body = json.dumps({
                "status": "ok",
                "python": sys.version,
                "cwd": os.getcwd(),
                "dir": os.listdir(os.path.dirname(__file__)),
                "sys_path": sys.path,
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            err = traceback.format_exc().encode()
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(err)))
            self.end_headers()
            self.wfile.write(err)

    def log_message(self, *args):
        pass