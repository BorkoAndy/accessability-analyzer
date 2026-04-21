# A11y Analyzer

Accessibility audit tool — axe-core + Lighthouse-style scoring via Python on Vercel.
Mimics the WAVE Chrome extension: sidebar categories, per-element snippets, WCAG tags, fix suggestions.

```
a11y-analyzer/
├── api/
│   ├── analyze.py       ← POST /api/analyze   (axe-core, URL or raw HTML)
│   ├── lighthouse.py    ← POST /api/lighthouse (Lighthouse-style, URL only)
│   └── health.py        ← GET  /api/health     (status + endpoint docs)
├── frontend/
│   └── index.html       ← standalone HTML+JS frontend, no build step
├── requirements.txt
└── vercel.json
```

---

## 1. Deploy API to Vercel

### Prerequisites
- [Vercel CLI](https://vercel.com/docs/cli): `npm i -g vercel`
- Python 3.11+ (Vercel handles this)

### Steps

```bash
cd a11y-analyzer
vercel login
vercel deploy --prod
```

Vercel will output a URL like `https://a11y-analyzer-xyz.vercel.app`.

> **Playwright on Vercel:** Vercel Python functions support Playwright via the `@vercel/python` builder.
> Chromium binaries are downloaded at function cold-start. First request may take ~10-15 seconds.
> Subsequent requests use the warm lambda and are much faster (~3-5s).

### Environment variables (optional)
None required. If you want to restrict origins, set `ALLOWED_ORIGINS` in Vercel dashboard
and update `_cors_headers()` in the API files.

---

## 2. Connect the frontend

Open `frontend/index.html` and update line 4 of the `<script>`:

```js
const API_BASE = 'https://YOUR-PROJECT.vercel.app';
```

Replace with your Vercel deployment URL (no trailing slash).

The frontend is a single HTML file — serve it anywhere:
- Open directly in browser (`file://`)
- Drop on GitHub Pages / Netlify / any static host
- Serve from your PHP backend (see below)

---

## 3. PHP backend (optional wrapper)

If you want to proxy calls through your PHP server instead of calling Vercel directly from
the browser (e.g. to hide the Vercel URL or add auth):

```php
<?php
// proxy.php — forwards requests to Vercel API

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$VERCEL = 'https://YOUR-PROJECT.vercel.app';
$endpoint = $_GET['endpoint'] ?? 'analyze'; // analyze | lighthouse | health

$body = file_get_contents('php://input');

$ch = curl_init("$VERCEL/api/$endpoint");
curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => $body,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
    CURLOPT_TIMEOUT        => 60,
]);

$response = curl_exec($ch);
$status   = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

http_response_code($status);
echo $response;
```

Then in `index.html` change:
```js
const API_BASE = 'https://your-php-site.com';
// and update fetch calls to use: /proxy.php?endpoint=analyze
```

---

## 4. API reference

### POST /api/analyze
Runs axe-core WCAG audit. Accepts URL **or** raw HTML.

**Request:**
```json
{ "url": "https://example.com" }
// OR
{ "html": "<!DOCTYPE html><html>...</html>" }
```

**Response:**
```json
{
  "url": "https://example.com",
  "score": 78,
  "summary": {
    "violations": 5,
    "errors": 3,
    "alerts": 2,
    "passes": 42,
    "needsReview": 4
  },
  "violations": [
    {
      "id": "image-alt",
      "impact": "critical",
      "description": "Ensures <img> elements have alternate text",
      "help": "Images must have alternate text",
      "helpUrl": "https://dequeuniversity.com/rules/axe/4.9/image-alt",
      "wcag": ["WCAG 2.0 A", "WCAG 2.1 A"],
      "nodeCount": 3,
      "snippets": ["<img src=\"hero.jpg\">"],
      "fixes": ["Element does not have an alt attribute"]
    }
  ],
  "passes": [...],
  "incomplete": [...]
}
```

### POST /api/lighthouse
Lighthouse-style multi-category audit. URL only.

**Request:** `{ "url": "https://example.com" }`

**Response:**
```json
{
  "url": "https://example.com",
  "scores": {
    "performance": 82,
    "accessibility": 74,
    "bestPractices": 100,
    "seo": 83
  },
  "performance": {
    "fcp": 1240,
    "loadTime": 2100,
    "resourceCount": 34,
    "transferSizeKB": 842.3,
    "jsHeapMB": 12
  },
  "seo": { "hasTitle": true, "hasDescription": false, ... },
  "bestPractices": { "https": true, "doctype": true, "deprecated": 0 },
  "axe": { "violations": 5, "passes": 42, "incomplete": 4 }
}
```

### GET /api/health
Returns API status and endpoint documentation.

---

## 5. Local development

```bash
pip install playwright requests beautifulsoup4
playwright install chromium

# Test analyze endpoint directly
python -c "
import api.analyze as a
# (simulate a request manually or use a local WSGI test runner)
"

# Or use Vercel dev server (runs Python functions locally)
vercel dev
```

---

## Engines used

| Engine | Role | License |
|--------|------|---------|
| [axe-core 4.9.1](https://github.com/dequelabs/axe-core) | WCAG 2.0/2.1/2.2 rules | MPL-2.0 (free) |
| [Playwright](https://playwright.dev) | Headless Chromium | Apache-2.0 (free) |
| Custom heuristics | Lighthouse-style perf/SEO/BP scoring | — |

For **full Lighthouse scores** (CLS, LCP, TBT etc.), run a Node.js serverless function
using the `lighthouse` npm package alongside this Python API.

---

## Accessibility categories (WAVE-style)

| Category | What it shows |
|----------|--------------|
| **Errors** | Critical + serious axe violations (WCAG failures) |
| **Alerts** | Moderate + minor violations (warnings) |
| **Passing** | Rules that passed |
| **Needs review** | Incomplete checks — axe couldn't determine pass/fail |
