import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class handler:
    @staticmethod
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Empty request body"}')
            return

        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data)
            url = data.get('url')
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        if not url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "URL required"}')
            return

        try:
            # 1. Fetch HTML using requests (Serverless friendly)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, timeout=12, headers=headers)
            resp.raise_for_status()
            html = resp.text
            soup = BeautifulSoup(html, 'html.parser')
            
            issues = []
            
            # ── HEURISTIC CHECKS (AXE-CORE STYLE) ──

            # 2. Images missing alt
            for img in soup.find_all('img'):
                if not img.has_attr('alt'):
                    issues.append({
                        "type": "errors", "impact": "critical", "rule": "image-alt",
                        "title": "Images must have alternate text",
                        "desc": "Ensures images have alternate text or a role of none or presentation",
                        "code": str(img)[:150],
                        "summary": "Fix: Element does not have an alt attribute"
                    })
            
            # 3. Buttons missing names
            for btn in soup.find_all(['button']):
                if not btn.get_text(strip=True) and not btn.get('aria-label') and not btn.get('title'):
                    issues.append({
                        "type": "errors", "impact": "critical", "rule": "button-name",
                        "title": "Buttons must have discernible text",
                        "desc": "Ensures buttons have discernible text so that they can be read by screen readers",
                        "code": str(btn)[:150]
                    })
            
            # 4. Input labels
            for inp in soup.find_all(['input', 'select', 'textarea']):
                if inp.get('type') == 'hidden': continue
                id_val = inp.get('id')
                has_label = False
                if id_val and soup.find('label', attrs={'for': id_val}): has_label = True
                if inp.find_parent('label'): has_label = True
                if inp.get('aria-label') or inp.get('aria-labelledby') or inp.get('title'): has_label = True
                
                if not has_label:
                    issues.append({
                        "type": "errors", "impact": "serious", "rule": "label",
                        "title": "Form elements must have labels",
                        "desc": "Ensures every form element has a label",
                        "code": str(inp)[:150]
                    })

            # 5. Missing Language
            if not soup.find('html', lang=True):
                issues.append({
                    "type": "alerts", "impact": "moderate", "rule": "html-has-lang",
                    "title": "<html> element must have a lang attribute",
                    "desc": "Ensures every HTML document has a lang attribute",
                    "code": "<html>"
                })

            # 6. Duplicate IDs
            ids = [tag.get('id') for tag in soup.find_all(id=True)]
            seen = set()
            duplicates = [x for x in ids if x in seen or seen.add(x)]
            for dup in set(duplicates):
                issues.append({
                    "type": "errors", "impact": "serious", "rule": "duplicate-id",
                    "title": "ID attribute value must be unique",
                    "desc": "Ensures every id attribute value is unique",
                    "code": f'id="{dup}"'
                })

            all_tags_count = len(soup.find_all())
            error_count = len([i for i in issues if i['type'] == 'errors'])
            score = int((1 - (error_count / (all_tags_count or 1))) * 100)

            response_data = {
                "url": url,
                "score": max(0, min(100, score)),
                "stats": {
                    "errors": error_count,
                    "alerts": len([i for i in issues if i['type'] == 'alerts']),
                    "passes": max(0, all_tags_count - len(issues))
                },
                "issues": issues,
                # Placeholder for Lighthouse (until separate call or combined)
                "lh": { "performance": 0, "accessibility": score, "bestPractices": 0, "seo": 0 }
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
