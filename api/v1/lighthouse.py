"""
/api/v1/lighthouse.py
Runs a lightweight Lighthouse-style audit via Playwright (v1).
Accepts POST with { url }
Accepts GET with ?url=...
"""

from http.server import BaseHTTPRequestHandler
import json
import time
from urllib.parse import urlparse, parse_qs
from lib.auth import check_auth

AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"


def _cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json",
    }


def _run_lighthouse_style(url: str) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )

        # ── Performance metrics ──────────────────────────────────────────────
        context = browser.new_context()
        page = context.new_page()

        t_start = time.time()
        response = page.goto(url, wait_until="load", timeout=30_000)
        lcp_approx = (time.time() - t_start) * 1000  # rough LCP proxy

        # Collect basic performance data
        perf = page.evaluate("""() => {
            const nav = performance.getEntriesByType('navigation')[0];
            const paint = performance.getEntriesByType('paint');
            const fcp = paint.find(p => p.name === 'first-contentful-paint');
            return {
                domContentLoaded: nav ? Math.round(nav.domContentLoadedEventEnd) : null,
                loadTime:         nav ? Math.round(nav.loadEventEnd) : null,
                transferSize:     nav ? nav.transferSize : null,
                fcp:              fcp ? Math.round(fcp.startTime) : null,
                resourceCount:    performance.getEntriesByType('resource').length,
                jsHeapUsed:       performance.memory ? Math.round(performance.memory.usedJSHeapSize/1024/1024) : null
            };
        }""")

        # ── SEO checks ───────────────────────────────────────────────────────
        seo = page.evaluate("""() => {
            const title = document.title;
            const desc  = document.querySelector('meta[name="description"]');
            const canonical = document.querySelector('link[rel="canonical"]');
            const viewport  = document.querySelector('meta[name="viewport"]');
            const h1s = document.querySelectorAll('h1');
            const imgs = Array.from(document.querySelectorAll('img'));
            const linksNoText = Array.from(document.querySelectorAll('a')).filter(a => !a.textContent.trim() && !a.getAttribute('aria-label'));
            return {
                hasTitle:        !!title && title.length > 0,
                titleLength:     title ? title.length : 0,
                hasDescription:  !!desc && !!desc.getAttribute('content'),
                hasCanonical:    !!canonical,
                hasViewport:     !!viewport,
                h1Count:         h1s.length,
                imgsWithoutAlt:  imgs.filter(i => !i.getAttribute('alt') && i.getAttribute('alt') !== '').length,
                totalImages:     imgs.length,
                emptyLinks:      linksNoText.length,
            };
        }""")

        # ── Best Practices checks ────────────────────────────────────────────
        best_practices = page.evaluate("""() => {
            const https = location.protocol === 'https:';
            const doctype = document.doctype !== null;
            const charset = document.characterSet;
            const deprecated = Array.from(document.querySelectorAll('marquee,blink,center,font,strike,tt')).length;
            return { https, doctype, charset, deprecated };
        }""")

        # ── Accessibility via axe ────────────────────────────────────────────
        page.add_script_tag(url=AXE_CDN)
        page.wait_for_function("typeof axe !== 'undefined'", timeout=10_000)
        axe_raw = page.evaluate("""async () => {
            const r = await axe.run();
            return { violations: r.violations.length, passes: r.passes.length, incomplete: r.incomplete.length };
        }""")

        browser.close()

    # ── Score computation (0-100) ────────────────────────────────────────────
    def perf_score():
        fcp = perf.get("fcp") or lcp_approx
        if fcp < 1800:   return 100
        if fcp < 3000:   return 75
        if fcp < 5000:   return 50
        return 25

    def a11y_score():
        v = axe_raw["violations"]
        return max(0, 100 - v * 5)

    def seo_score():
        checks = [
            seo["hasTitle"] and 10 <= seo["titleLength"] <= 70,
            seo["hasDescription"],
            seo["hasViewport"],
            seo["h1Count"] == 1,
            seo["imgsWithoutAlt"] == 0,
            seo["emptyLinks"] == 0,
        ]
        return round(sum(checks) / len(checks) * 100)

    def bp_score():
        checks = [
            best_practices["https"],
            best_practices["doctype"],
            best_practices["deprecated"] == 0,
        ]
        return round(sum(checks) / len(checks) * 100)

    return {
        "url": url,
        "scores": {
            "performance":    perf_score(),
            "accessibility":  a11y_score(),
            "bestPractices":  bp_score(),
            "seo":            seo_score(),
        },
        "performance": {
            "fcp":            perf.get("fcp"),
            "loadTime":       perf.get("loadTime"),
            "resourceCount":  perf.get("resourceCount"),
            "transferSizeKB": round(perf["transferSize"] / 1024, 1) if perf.get("transferSize") else None,
            "jsHeapMB":       perf.get("jsHeapUsed"),
        },
        "seo":           seo,
        "bestPractices": best_practices,
        "axe": {
            "violations": axe_raw["violations"],
            "passes":     axe_raw["passes"],
            "incomplete": axe_raw["incomplete"],
        },
    }


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in _cors_headers().items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        """Handle GET requests with ?url= query parameter."""
        if not check_auth(self):
            return
        try:
            query = urlparse(self.path).query
            params = parse_qs(query)
            url = params.get("url", [""])[0].strip()

            if not url:
                self._respond(400, {"error": "Provide 'url' parameter"})
                return

            result = _run_lighthouse_style(url)
            self._respond(200, result)

        except Exception as e:
            self._respond(500, {"error": str(e)})

    def do_POST(self):
        if not check_auth(self):
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length))
            url    = body.get("url", "").strip()
            if not url:
                self._respond(400, {"error": "Provide 'url'"})
                return
            result = _run_lighthouse_style(url)
            self._respond(200, result)
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        for k, v in _cors_headers().items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass
