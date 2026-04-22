import json
import requests
from bs4 import BeautifulSoup
import time

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
            self.end_headers()
            self.wfile.write(b'{"error": "URL required"}')
            return

        try:
            # 1. Fetch HTML
            start_time = time.time()
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            resp = requests.get(url, timeout=10, headers=headers)
            resp.raise_for_status()
            load_time = time.time() - start_time
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 1. Performance Heuristics (Timing)
            perf_score = max(0, min(100, 100 - (load_time * 12)))
            
            # 2. SEO Heuristics
            seo_score = 0
            if soup.find('title'): seo_score += 25
            if soup.find('meta', attrs={'name': 'description'}): seo_score += 25
            if soup.find('h1'): seo_score += 25
            if soup.find('meta', attrs={'name': 'viewport'}): seo_score += 25
            
            # 3. Best Practices
            bp_score = 0
            if url.startswith('https'): bp_score += 50
            if soup.find('link', attrs={'rel': 'icon'}): bp_score += 50
            
            scores = {
                "performance": int(perf_score),
                "accessibility": 100, # Placeholder
                "bestPractices": bp_score,
                "seo": seo_score
            }

            body = json.dumps(scores).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
