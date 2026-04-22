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
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"error": "URL required"}')
            return

        try:
            req_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            start_time = time.time()
            resp = requests.get(url, timeout=12, headers=req_headers)
            resp.raise_for_status()
            load_time = time.time() - start_time

            soup = BeautifulSoup(resp.text, 'html.parser')
            audits = []

            # 1. Performance
            perf_score = max(0, min(100, int(100 - (load_time * 15))))
            if load_time < 2:
                audits.append({"cat": "perf", "title": "Good Response Time", "score": 1, "desc": f"The page loaded in {load_time:.2f}s."})
            elif load_time < 4:
                audits.append({"cat": "perf", "title": "Slow Response Time", "score": 0.5, "desc": f"The page took {load_time:.2f}s. Aim for under 2s."})
            else:
                audits.append({"cat": "perf", "title": "Very Slow Response Time", "score": 0, "desc": f"The page took {load_time:.2f}s to load. This will harm user experience."})

            # 2. SEO
            seo_score = 0

            title = soup.find('title')
            if title:
                t_len = len(title.text)
                if 10 <= t_len <= 70:
                    seo_score += 20
                    audits.append({"cat": "seo", "title": "Optimal Title Length", "score": 1, "desc": f"Title is {t_len} chars (ideal: 10–70)."})
                else:
                    seo_score += 10
                    audits.append({"cat": "seo", "title": "Suboptimal Title Length", "score": 0.5, "desc": f"Title is {t_len} chars. Ideal range is 10–70."})
            else:
                audits.append({"cat": "seo", "title": "Missing Title Tag", "score": 0, "desc": "Each page needs a <title> tag for search engines."})

            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                d_len = len(meta_desc.get('content', ''))
                if 50 <= d_len <= 160:
                    seo_score += 20
                    audits.append({"cat": "seo", "title": "Optimal Description Length", "score": 1, "desc": f"Description is {d_len} chars (ideal: 50–160)."})
                else:
                    seo_score += 10
                    audits.append({"cat": "seo", "title": "Suboptimal Description Length", "score": 0.5, "desc": f"Description is {d_len} chars. Ideal is 50–160."})
            else:
                audits.append({"cat": "seo", "title": "Missing Meta Description", "score": 0, "desc": "Meta descriptions help search engines display relevant snippets."})

            if soup.find('link', attrs={'rel': 'canonical'}):
                seo_score += 20
                audits.append({"cat": "seo", "title": "Canonical Tag Present", "score": 1, "desc": "Prevents duplicate content issues in search engines."})
            else:
                audits.append({"cat": "seo", "title": "Missing Canonical Tag", "score": 0, "desc": "Add <link rel='canonical'> to define the preferred URL."})

            if soup.find('h1'):
                seo_score += 20
                audits.append({"cat": "seo", "title": "H1 Heading Present", "score": 1, "desc": "Page has a primary heading, good for structure and SEO."})
            else:
                audits.append({"cat": "seo", "title": "Missing H1 Heading", "score": 0, "desc": "Each page should have exactly one <h1> heading."})

            if soup.find('meta', attrs={'name': 'viewport'}):
                seo_score += 20
                audits.append({"cat": "seo", "title": "Viewport Meta Present", "score": 1, "desc": "Correctly configured for mobile devices."})
            else:
                audits.append({"cat": "seo", "title": "Missing Viewport Meta", "score": 0, "desc": "Add <meta name='viewport'> for responsive design."})

            # 3. Best Practices
            bp_score = 0

            if url.startswith('https'):
                bp_score += 40
                audits.append({"cat": "bp", "title": "Uses HTTPS", "score": 1, "desc": "Site is served over a secure, encrypted connection."})
            else:
                audits.append({"cat": "bp", "title": "Not Using HTTPS", "score": 0, "desc": "Migrate to HTTPS to protect users and improve search ranking."})

            if soup.contents and '!DOCTYPE' in str(soup.contents[0]).upper():
                bp_score += 20
                audits.append({"cat": "bp", "title": "Valid Doctype Declared", "score": 1, "desc": "Prevents browser quirks mode."})
            else:
                audits.append({"cat": "bp", "title": "Missing or Invalid Doctype", "score": 0, "desc": "Add <!DOCTYPE html> as the very first line."})

            if soup.find('meta', charset=True) or soup.find('meta', attrs={'http-equiv': 'Content-Type'}):
                bp_score += 20
                audits.append({"cat": "bp", "title": "Character Encoding Declared", "score": 1, "desc": "Character set is explicitly defined."})
            else:
                audits.append({"cat": "bp", "title": "Missing Character Encoding", "score": 0, "desc": "Add <meta charset='UTF-8'> in the <head> section."})

            if soup.find('link', attrs={'rel': 'icon'}):
                bp_score += 20
                audits.append({"cat": "bp", "title": "Favicon Present", "score": 1, "desc": "Helps with branding in browser tabs and bookmarks."})
            else:
                audits.append({"cat": "bp", "title": "No Favicon", "score": 0, "desc": "Add <link rel='icon' href='/favicon.ico'> to the <head>."})

            response_data = {
                "scores": {
                    "performance": perf_score,
                    "accessibility": 0, # Placeholder, synchronized by frontend
                    "bestPractices": max(0, bp_score),
                    "seo": max(0, seo_score)
                },
                "audits": audits
            }

            body = json.dumps(response_data).encode()
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
