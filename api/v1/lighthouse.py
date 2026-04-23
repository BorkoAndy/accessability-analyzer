import json
import requests
from bs4 import BeautifulSoup
import time

class Logic:
    @staticmethod
    def run_audit(url):
        req_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        start_time = time.time()
        resp = requests.get(url, timeout=12, headers=req_headers, allow_redirects=True)
        resp.raise_for_status()
        load_time = time.time() - start_time
        final_url = resp.url

        soup = BeautifulSoup(resp.text, 'html.parser')
        audits = []

        # 1. Performance
        perf_score = max(0, min(100, int(100 - (load_time * 15))))
        if load_time < 2:
            audits.append({"cat": "perf", "title": "Good Response Time", "score": 1, "desc": f"The page loaded in {load_time:.2f}s."})
        elif load_time < 4:
            audits.append({"cat": "perf", "title": "Slow Response Time", "score": 0.5, "desc": f"The page took {load_time:.2f}s. Aim for under 2s."})
        else:
            audits.append({"cat": "perf", "title": "Very Slow Response Time", "score": 0, "desc": f"The page took {load_time:.2f}s to load."})

        # 2. SEO
        seo_score = 0
        title = soup.find('title')
        if title:
            t_len = len(title.text)
            if 10 <= t_len <= 70:
                seo_score += 20
                audits.append({"cat": "seo", "title": "Optimal Title Length", "score": 1, "desc": f"Title is {t_len} chars."})
            else:
                seo_score += 10
                audits.append({"cat": "seo", "title": "Suboptimal Title Length", "score": 0.5, "desc": f"Title is {t_len} chars."})
        else:
            audits.append({"cat": "seo", "title": "Missing Title Tag", "score": 0, "desc": "Missing <title>."})

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            d_len = len(meta_desc.get('content', ''))
            if 50 <= d_len <= 160:
                seo_score += 20
                audits.append({"cat": "seo", "title": "Optimal Description Length", "score": 1})
            else:
                seo_score += 10
                audits.append({"cat": "seo", "title": "Suboptimal Description Length", "score": 0.5})
        else:
            audits.append({"cat": "seo", "title": "Missing Meta Description", "score": 0})

        if soup.find('link', attrs={'rel': 'canonical'}): seo_score += 20
        if soup.find('h1'): seo_score += 20
        if soup.find('meta', attrs={'name': 'viewport'}): seo_score += 20

        # 3. Best Practices
        bp_score = 0
        if final_url.startswith('https'): bp_score += 40
        if soup.contents and '!DOCTYPE' in str(soup.contents[0]).upper(): bp_score += 20
        if soup.find('meta', charset=True) or soup.find('meta', attrs={'http-equiv': 'Content-Type'}): bp_score += 20
        if soup.find('link', attrs={'rel': 'icon'}): bp_score += 20

        return {
            "url": final_url,
            "scores": {
                "performance": perf_score,
                "accessibility": 0,
                "bestPractices": max(0, bp_score),
                "seo": max(0, seo_score)
            },
            "audits": audits
        }

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
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"error": "URL required"}')
            return

        try:
            results = Logic.run_audit(url)
            body = json.dumps(results).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
