"""
/api/v1/analyze.py
Main accessibility analysis endpoint (v1).
Accepts POST with { url } or { html }
Accepts GET with ?url=...
Returns axe-core violations, passes, incomplete + summary scores.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import tempfile
from urllib.parse import urlparse, parse_qs
from auth import check_auth

# ── axe-core CDN (pinned version, no npm needed) ──────────────────────────────
AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"

# ── WCAG level labels ─────────────────────────────────────────────────────────
WCAG_TAGS = {
    "wcag2a":   "WCAG 2.0 A",
    "wcag2aa":  "WCAG 2.0 AA",
    "wcag21a":  "WCAG 2.1 A",
    "wcag21aa": "WCAG 2.1 AA",
    "wcag22aa": "WCAG 2.2 AA",
    "best-practice": "Best Practice",
    "section508": "Section 508",
}

SEVERITY_ORDER = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}

def _cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json",
    }

def _route(self):
    path = urlparse(self.path).path.rstrip("/")

    if path == "/api/v1/analyze":
        analyze_handler(self.request, self.client_address, self.server).handle()
    elif path == "/api/v1/lighthouse":
        lighthouse_handler(self.request, self.client_address, self.server).handle()
    elif path == "/api/v1/health":
        health_handler(self.request, self.client_address, self.server).handle()
    else:
        self.send_response(404)
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())


def _run_axe(playwright, target_url: str | None, html: str | None) -> dict:
    """Launch Chromium, inject axe-core, return raw axe results."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        )
        page = browser.new_page()

        if html:
            # Write to a temp file so relative resources resolve
            with tempfile.NamedTemporaryFile(
                suffix=".html", mode="w", delete=False, encoding="utf-8"
            ) as f:
                f.write(html)
                tmp_path = f.name
            page.goto(f"file://{tmp_path}")
        else:
            page.goto(target_url, wait_until="networkidle", timeout=30_000)

        # Inject axe-core from CDN
        page.add_script_tag(url=AXE_CDN)
        page.wait_for_function("typeof axe !== 'undefined'", timeout=10_000)

        # Run full axe audit
        results = page.evaluate("""
            async () => {
                const results = await axe.run(document, {
                    runOnly: {
                        type: 'tag',
                        values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice','section508']
                    },
                    resultTypes: ['violations', 'passes', 'incomplete']
                });
                return {
                    violations:  results.violations,
                    passes:      results.passes,
                    incomplete:  results.incomplete,
                    testEngine:  results.testEngine,
                    url:         results.url
                };
            }
        """)

        browser.close()
        return results


def _score(violations: list) -> int:
    """
    Accessibility score 0–100, similar to Lighthouse's a11y scoring.
    Weighted by impact: critical=4, serious=3, moderate=2, minor=1
    """
    weights = {"critical": 4, "serious": 3, "moderate": 2, "minor": 1}
    penalty = sum(
        weights.get(v.get("impact", "minor"), 1) * len(v.get("nodes", []))
        for v in violations
    )
    score = max(0, 100 - penalty * 3)
    return score


def _wcag_labels(tags: list) -> list:
    return [WCAG_TAGS[t] for t in tags if t in WCAG_TAGS]


def _format_violation(v: dict) -> dict:
    nodes = v.get("nodes", [])
    snippets = [n.get("html", "") for n in nodes[:3]]
    fixes = []
    for node in nodes[:3]:
        any_checks = node.get("any", []) + node.get("all", []) + node.get("none", [])
        for chk in any_checks[:1]:
            if chk.get("message"):
                fixes.append(chk["message"])
    return {
        "id":          v.get("id"),
        "impact":      v.get("impact"),
        "description": v.get("description"),
        "help":        v.get("help"),
        "helpUrl":     v.get("helpUrl"),
        "wcag":        _wcag_labels(v.get("tags", [])),
        "nodeCount":   len(nodes),
        "snippets":    snippets,
        "fixes":       fixes,
    }


def _format_pass(p: dict) -> dict:
    return {
        "id":          p.get("id"),
        "description": p.get("description"),
        "wcag":        _wcag_labels(p.get("tags", [])),
        "nodeCount":   len(p.get("nodes", [])),
    }


def _build_response(raw: dict, target: str) -> dict:
    violations  = sorted(raw["violations"],  key=lambda v: SEVERITY_ORDER.get(v.get("impact","minor"), 3))
    passes      = raw["passes"]
    incomplete  = raw["incomplete"]

    score = _score(violations)

    # Category breakdown (like WAVE sidebar)
    categories = {
        "Errors":       [v for v in violations if v.get("impact") in ("critical","serious")],
        "Alerts":       [v for v in violations if v.get("impact") in ("moderate","minor")],
        "Needs review": incomplete,
    }

    return {
        "url":        target,
        "engine":     raw.get("testEngine", {}),
        "score":      score,
        "summary": {
            "violations": len(violations),
            "errors":     len(categories["Errors"]),
            "alerts":     len(categories["Alerts"]),
            "passes":     len(passes),
            "needsReview":len(incomplete),
        },
        "violations":  [_format_violation(v) for v in violations],
        "passes":      [_format_pass(p) for p in passes],
        "incomplete":  [_format_violation(v) for v in incomplete],
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

            raw = _run_axe(None, url, None)
            result = _build_response(raw, url)
            self._respond(200, result)

        except Exception as e:
            self._respond(500, {"error": str(e)})

    def do_POST(self):
        if not check_auth(self):
            return
        try:
            length  = int(self.headers.get("Content-Length", 0))
            body    = json.loads(self.rfile.read(length))
            url     = body.get("url", "").strip()
            html    = body.get("html", "").strip()

            if not url and not html:
                self._respond(400, {"error": "Provide 'url' or 'html'"})
                return

            raw    = _run_axe(None, url or None, html or None)
            target = url or "Pasted HTML"
            result = _build_response(raw, target)

            self._respond(200, result)

        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        for k, v in _cors_headers().items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # silence default stdout logging
