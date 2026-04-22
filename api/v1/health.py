import json

class handler:
    @staticmethod
    def do_GET(self):
        body = json.dumps({
            "status": "online",
            "version": "1.0.0",
            "capabilities": ["axe-core", "heuristics"]
        }).encode()
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
