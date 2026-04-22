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
            audits = []

            # 1. Performance
            perf_score = max(0, min(100, int(100 - (load_time * 15))))
            if load_time < 2:
                audits.append({"cat": "perf", "title": "Good Response Time", "score": 1, "desc": f"The page loaded in {load_time:.1f}s."})
            else:
                audits.append({"cat": "perf", "title": "Slow Response Time", "score": 0, "desc": f"The page took {load_time:.1f}s to load. Aim for under 2s."})

            # 2. SEO
            seo_score = 0
            # Title
            title = soup.find('title')
            if title:
                t_len = len(title.text)
                if t_len >= 10 and t_len <= 70:
                    seo_score += 20
                    audits.append({"cat": "seo", "title": "Optimal Title Length", "score": 1, "desc": "Document title is between 10 and 70 characters."})
                else:
                    seo_score += 10
                    audits.append({"cat": "seo", "title": "Suboptimal Title Length", "score": 0.5, "desc": f"Title is {t_len} chars. Aim for 10-70."})
            else:
                audits.append({"cat": "seo", "title": "Missing Title Tag", "score": 0, "desc": "Every page needs a <title> for search engines."})

            # Meta Description
            desc = soup.find('meta', attrs={'name': 'description'})
            if desc:
                d_len = len(desc.get('content', ''))
                if d_len >= 50 and d_len <= 160:
                    seo_score += 20
                    audits.append({"cat": "seo", "title": "Optimal Description Length", "score": 1, "desc": "Meta description is well-sized."})
                else:
                    seo_score += 10
                    audits.append({"cat": "seo", "title": "Suboptimal Description Length", "score": 0.5, "desc": f"Description is {d_len} chars. Aim for 50-160."})
            else:
                audits.append({"cat": "seo", "title": "Missing Meta Description", "score": 0, "desc": "Descriptions help users find your content in search results."})

            # Canonical
            if soup.find('link', attrs={'rel': 'canonical'}):
                seo_score += 20
                audits.append({"cat": "seo", "title": "Canonical Tag Present", "score": 1, "desc": "Prevents duplicate content issues."})
            else:
                audits.append({"cat": "seo", "title": "Missing Canonical Tag", "score": 0, "desc": "Add a canonical link to define the preferred version of this page."})

            # H1
            if soup.find('h1'):
                seo_score += 20
                audits.append({"cat": "seo", "title": "H1 Heading Present", "score": 1, "desc": "Page has a primary heading for structure."})
            else:
                audits.append({"cat": "seo", "title": "Missing H1 Heading", "score": 0, "desc": "Each page should have one main <h1>."})

            # Viewport
            if soup.find('meta', attrs={'name': 'viewport'}):
                seo_score += 20
                audits.append({"cat": "seo", "title": "Viewport Meta Present", "score": 1, "desc": "Mobile users context is defined."})
            else:
                audits.append({"cat": "seo", "title": "Missing Viewport Meta", "score": 0, "desc": "Essential for responsive design."})

            # 3. Best Practices
            bp_score = 0
            if url.startswith('https'):
                bp_score += 40
                audits.append({"cat": "bp", "title": "Uses HTTPS", "score": 1, "desc": "Site is served over a secure connection."})
            else:
                audits.append({"cat": "bp", "title": "Does Not Use HTTPS", "score": 0, "desc": "Switch to HTTPS to protect user data and improve trust."})

            if soup.contents and '!DOCTYPE html' in str(soup.contents[0]).lower():
                bp_score += 20
                audits.append({"cat": "bp", "title": "Valid Doctype", "score": 1, "desc": "Prevents the browser from switching to quirks mode."})
            else:
                audits.append({"cat": "bp", "title": "Missing Doctype", "score": 0, "desc": "Add <!DOCTYPE html> at the top of the HTML."})

            if soup.find('meta', charset=True) or soup.find('meta', attrs={'http-equiv': 'Content-Type'}):
                bp_score += 20
                audits.append({"cat": "bp", "title": "Character Encoding Defined", "score": 1, "desc": "Prevents text rendering issues."})
            else:
                audits.append({"cat": "bp", "title": "Charset Not Defined", "score": 0, "desc": "Add <meta charset='UTF-8'> in the <head>."})

            if soup.find('link', attrs={'rel': 'icon'}):
                bp_score += 20
                audits.append({"cat": "bp", "title": "Favicon Present", "score": 1, "desc": "Helps users identify your site in browser tabs."})
            else:
                audits.append({"cat": "bp", "title": "Missing Favicon", "score": 0, "desc": "Add a shortcut icon link for better branding."})

            response_data = {
                "scores": {
                    "performance": perf_score,
                    "accessibility": 100, # Handled by analyze.py
                    "bestPractices": max(0, bp_score),
                    "seo": max(0, seo_score)
                },
                "audits": audits
            }

            body = json.dumps(response_data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
