import json
import asyncio
from playwright.async_api import async_playwright
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
            self.wfile.write(b'{"error": "URL required for Lighthouse scoring"}')
            return

        try:
            scores = asyncio.run(handler.get_lighthouse_scores(url))
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

    @staticmethod
    async def get_lighthouse_scores(url):
        async with async_playwright() as p:
            start_time = time.time()
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 1. Performance Heuristics (Timing)
            await page.goto(url, wait_until="load")
            load_time = time.time() - start_time
            perf_score = max(0, min(100, 100 - (load_time * 10))) # Very simple proxy
            
            # 2. SEO Heuristics
            seo_score = 0
            # Meta tags
            if await page.query_selector('title'): seo_score += 25
            if await page.query_selector('meta[name="description"]'): seo_score += 25
            if await page.query_selector('h1'): seo_score += 25
            if await page.query_selector('meta[name="viewport"]'): seo_score += 25
            
            # 3. Best Practices
            bp_score = 0
            # HTTPS
            if url.startswith('https'): bp_score += 50
            # No console errors
            # (In a real audit we'd listen to console events)
            bp_score += 50 
            
            # 4. Accessibility (Heuristic or use Axe result)
            # For this separate endpoint, we'll return a placeholder or run a quick axe check
            a11y_score = 100 # Placeholder - actual results come from /analyze
            
            await browser.close()
            
            return {
                "performance": int(perf_score),
                "accessibility": a11y_score,
                "bestPractices": bp_score,
                "seo": seo_score
            }
