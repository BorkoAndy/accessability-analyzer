import json
import os
import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urlparse

# Use a stable CDN for axe-core
AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"

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
            html = data.get('html')
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        if not url and not html:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "URL or HTML required"}')
            return

        # Run Playwright in an async loop
        try:
            results = asyncio.run(handler.run_axe(url, html))
            
            # Summarize results for the frontend dashboard
            violations = results.get('violations', [])
            passes = results.get('passes', [])
            incomplete = results.get('incomplete', [])
            
            # Simple scoring heuristic
            total_rules = len(violations) + len(passes)
            score = int((len(passes) / total_rules * 100)) if total_rules > 0 else 100
            
            # Format issues for the frontend cards
            formatted_issues = []
            for v in violations:
                for node in v.get('nodes', []):
                    formatted_issues.append({
                        "type": "errors",
                        "impact": v.get('impact', 'serious'),
                        "rule": v.get('id'),
                        "title": v.get('help'),
                        "desc": v.get('description'),
                        "code": node.get('html'),
                        "summary": node.get('failureSummary')
                    })
            
            for v in incomplete:
                for node in v.get('nodes', []):
                    formatted_issues.append({
                        "type": "alerts",
                        "impact": v.get('impact', 'moderate'),
                        "rule": v.get('id'),
                        "title": v.get('help'),
                        "desc": v.get('description'),
                        "code": node.get('html'),
                        "summary": node.get('failureSummary')
                    })

            response_data = {
                "url": url or "Raw HTML",
                "score": score,
                "stats": {
                    "errors": len([i for i in formatted_issues if i['type'] == 'errors']),
                    "alerts": len([i for i in formatted_issues if i['type'] == 'alerts']),
                    "passes": len(passes)
                },
                "issues": formatted_issues,
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

    @staticmethod
    async def run_axe(url, html):
        async with async_playwright() as p:
            # We use chromium as it's best for axe-core
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            if url:
                await page.goto(url, wait_until="networkidle", timeout=20000)
            else:
                await page.set_content(html)
            
            # Inject Axe-Core from CDN
            await page.add_script_tag(url=AXE_CDN)
            
            # Run Axe analysis
            results = await page.evaluate("axe.run()")
            await browser.close()
            return results
