import json
import requests

class handler:
    @staticmethod
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            url = data.get('url')
        except:
            url = None

        if not url:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "URL required"}).encode())
            return

        try:
            req_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            # Add https:// if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            resp = requests.get(url, timeout=10, headers=req_headers, allow_redirects=True)
            
            self.send_response(200)
            self.send_header('Content-Type', resp.headers.get('Content-Type', 'text/html'))
            self.end_headers()
            self.wfile.write(resp.content)
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
