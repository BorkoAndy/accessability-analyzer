import json
import requests
from bs4 import BeautifulSoup
import re

class handler:
    @staticmethod
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_response(400)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"error": "Empty request body"}')
            return

        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data)
            url = data.get('url')
        except Exception:
            self.send_response(400)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        if not url:
            self.send_response(400)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"error": "URL required"}')
            return

        try:
            req_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, timeout=12, headers=req_headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            issues = []
            
            # ── SHARP RULES (WCAG 2.1 ALIGNED) ──

            # 1. Images (Detailed)
            for img in soup.find_all('img'):
                if not img.has_attr('alt'):
                    issues.append({
                        "type": "errors", "impact": "critical", "rule": "image-alt",
                        "title": "Images must have alternate text",
                        "desc": "Ensures every image has a descriptive alt attribute or role='presentation'.",
                        "code": str(img)[:150]
                    })
                elif img.get('alt'):
                    alt_text = img.get('alt')
                    if alt_text.count(',') > 4 or len(alt_text.split()) > 20:
                        issues.append({
                            "type": "alerts", "impact": "moderate", "rule": "alt-stuffing",
                            "title": "Suspicious alt text (Keyword Stuffing)",
                            "desc": "Alt text should describe the image, not be a list of SEO keywords.",
                            "code": f'alt="{alt_text[:100]}..."'
                        })

            # 2. Links
            for a in soup.find_all('a'):
                content = a.get_text(strip=True)
                imgs = a.find_all('img')
                if not content and imgs:
                    for img in imgs:
                        if not img.get('alt'):
                            issues.append({
                                "type": "errors", "impact": "critical", "rule": "link-name",
                                "title": "Link with image must have alt text",
                                "desc": "Links containing only an image need descriptive alt text on the image.",
                                "code": str(a)[:150]
                            })
                elif not content and not a.get('aria-label') and not a.get('title'):
                    if not a.find_all():
                        issues.append({
                            "type": "errors", "impact": "serious", "rule": "link-name",
                            "title": "Links must have discernible text",
                            "desc": "Ensures links have text or ARIA labels for screen readers.",
                            "code": str(a)[:150]
                        })

            # 3. Forms
            for inp in soup.find_all(['input', 'select', 'textarea']):
                itype = inp.get('type', '').lower()
                if itype in ['hidden', 'submit', 'button', 'reset', 'image']:
                    if itype == 'image' and not inp.get('alt'):
                        issues.append({
                            "type": "errors", "impact": "critical", "rule": "input-image-alt",
                            "title": "Image buttons must have alt text",
                            "desc": "Graphical submit buttons (<input type='image'>) require descriptive alt text.",
                            "code": str(inp)[:150]
                        })
                    continue
                
                id_val = inp.get('id')
                has_label = False
                if id_val and soup.find('label', attrs={'for': id_val}): has_label = True
                if inp.find_parent('label'): has_label = True
                if inp.get('aria-label') or inp.get('aria-labelledby') or inp.get('title'): has_label = True
                
                if not has_label:
                    issues.append({
                        "type": "errors", "impact": "serious", "rule": "label",
                        "title": "Form elements must have labels",
                        "desc": "Ensures every form element is programmatically associated with a label.",
                        "code": str(inp)[:150]
                    })

            # 4. Global Metadata
            if not soup.find('html', lang=True):
                issues.append({
                    "type": "errors", "impact": "serious", "rule": "html-has-lang",
                    "title": "<html> element must have a lang attribute",
                    "desc": "Screen readers need a lang attribute to use the correct pronunciation.",
                    "code": "<html>"
                })
            
            if not soup.find('meta', attrs={'name': 'viewport'}):
                issues.append({
                    "type": "alerts", "impact": "moderate", "rule": "viewport",
                    "title": "Missing viewport meta tag",
                    "desc": "A viewport tag is essential for mobile accessibility.",
                    "code": "<head>"
                })

            # 5. Headings Hierarchy
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if not soup.find('h1'):
                issues.append({
                    "type": "errors", "impact": "serious", "rule": "page-has-heading-one",
                    "title": "Page should contain one <h1> heading",
                    "desc": "An H1 helps users and search engines understand the page's main topic.",
                    "code": "<body>"
                })
            
            last_level = 0
            for h in headings:
                level = int(h.name[1])
                if last_level > 0 and level > last_level + 1:
                    issues.append({
                        "type": "alerts", "impact": "moderate", "rule": "heading-order",
                        "title": f"Heading levels should not skip ({h.name} follows h{last_level})",
                        "desc": "Heading levels should increase by only one at a time for proper structure.",
                        "code": str(h)[:100]
                    })
                last_level = level

            # 6. Iframes and Image Maps
            for f in soup.find_all(['iframe', 'frame']):
                if not f.get('title'):
                    issues.append({
                        "type": "errors", "impact": "serious", "rule": "frame-title",
                        "title": "Frames must have a title attribute",
                        "desc": "Iframes need titles so screen reader users know what they contain.",
                        "code": str(f)[:150]
                    })
            
            for area in soup.find_all('area'):
                if not area.get('alt'):
                    issues.append({
                        "type": "errors", "impact": "critical", "rule": "area-alt",
                        "title": "Image map <area> elements must have alt text",
                        "desc": "Area elements in image maps serve as links and need descriptive alt text.",
                        "code": str(area)[:150]
                    })

            # ── PENALTY-BASED SCORING ──
            all_tags = soup.find_all()
            base_score = 100
            penalties = {"critical": 15, "serious": 8, "moderate": 3, "minor": 1}
            
            unique_rules = {}
            for i in issues:
                rule = i['rule']
                impact = i['impact']
                if rule not in unique_rules or penalties[impact] > penalties[unique_rules[rule]]:
                    unique_rules[rule] = impact
            
            total_penalty = sum(penalties[imp] for imp in unique_rules.values())
            final_score = max(0, base_score - total_penalty)

            response_data = {
                "url": url,
                "score": final_score,
                "stats": {
                    "errors": len([i for i in issues if i['type'] == 'errors']),
                    "alerts": len([i for i in issues if i['type'] == 'alerts']),
                    "passes": max(0, len(all_tags) - len(issues))
                },
                "issues": issues,
                "lh": {"performance": 0, "accessibility": final_score, "bestPractices": 0, "seo": 0}
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
