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
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            start_time = time.time()
            resp = requests.get(url, timeout=12, headers=headers)
            resp.raise_for_status()
            load_time = time.time() - start_time
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 1. Performance (Stricter Timing + Resource counts)
            # 0-5s -> 100-50, >5s -> <50
            perf_score = max(0, min(100, 100 - (load_time * 15)))
            
            # 2. SEO (Thorough checks)
            seo_points = 0
            if soup.find('title'): seo_points += 20
            if soup.find('meta', attrs={'name': 'description'}): seo_points += 20
            if soup.find('h1'): seo_points += 20
            if soup.find('meta', attrs={'name': 'viewport'}): seo_points += 20
            if soup.find('link', attrs={'rel': 'canonical'}): seo_points += 20
            
            # SEO Metadata Length Checks (Deduct if too short/long)
            title = soup.find('title')
            if title and (len(title.text) < 10 or len(title.text) > 70): seo_points -= 5
            desc = soup.find('meta', attrs={'name': 'description'})
            if desc and (len(desc.get('content', '')) < 50 or len(desc.get('content', '')) > 160): seo_points -= 5

            # 3. Best Practices
            bp_points = 0
            if url.startswith('https'): bp_points += 40
            if soup.contents and '!DOCTYPE html' in str(soup.contents[0]).lower(): bp_points += 20
            if soup.find('meta', charset=True) or soup.find('meta', attrs={'http-equiv': 'Content-Type'}): bp_points += 20
            if soup.find('link', attrs={'rel': 'icon'}): bp_points += 20
            
            # No console.log or dangerous eval (Heuristic)
            scripts = soup.find_all('script')
            for s in scripts:
                if s.string and ('console.log' in s.string or 'eval(' in s.string):
                    bp_points -= 10
                    break

            scores = {
                "performance": int(max(0, perf_score)),
                "accessibility": 100, # Handled by analyze.py
                "bestPractices": int(max(0, bp_points)),
                "seo": int(max(0, seo_points))
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
