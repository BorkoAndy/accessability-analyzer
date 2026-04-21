# A11y Analyzer

Accessibility audit tool — axe-core + Lighthouse-style scoring via Python on Vercel.
Mimics the WAVE Chrome extension: sidebar categories, per-element snippets, WCAG tags, fix suggestions.

```
a11y-analyzer/
├── api/
│   └── v1/
│       ├── analyze.py       ← GET/POST /api/v1/analyze    (axe-core, URL or raw HTML)
│       ├── lighthouse.py    ← GET/POST /api/v1/lighthouse (Lighthouse-style, URL only)
│       └── health.py        ← GET /api/v1/health          (status + endpoint docs)
├── frontend/
│   └── index.html           ← standalone HTML+JS frontend
├── requirements.txt
└── vercel.json
```

---

## 1. Deploy to Vercel

### Prerequisites
- [Vercel CLI](https://vercel.com/docs/cli): `npm i -g vercel`
- Python 3.11+ (Vercel handles this)

### Steps

```bash
cd a11y-analyzer
vercel login
vercel deploy --prod
```

Vercel will output a URL like `https://a11y-analyzer.vercel.app`.

---

## 2. API Reference (v1)

### /api/v1/analyze
Runs axe-core WCAG audit. 

- **POST**: Send `{ "url": "..." }` or `{ "html": "..." }` in JSON body.
- **GET**: Send `?url=...` as a query parameter.

**Response Example:**
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
  "violations": [...]
}
```

### /api/v1/lighthouse
Lighthouse-style multi-category audit. **URL only.**

- **POST**: Send `{ "url": "..." }` in JSON body.
- **GET**: Send `?url=...` as a query parameter.

**Response Example:**
```json
{
  "url": "https://example.com",
  "scores": {
    "performance": 82,
    "accessibility": 74,
    "bestPractices": 100,
    "seo": 83
  }
}
```

### /api/v1/health
Returns API status, version, and endpoint documentation.

---

## 3. Local development

```bash
pip install playwright requests beautifulsoup4
playwright install chromium

# Run Vercel dev server (runs Python functions locally)
vercel dev
```

---

## Engines used

| Engine | Role | License |
|--------|------|---------|
| [axe-core 4.9.1](https://github.com/dequelabs/axe-core) | WCAG 2.0/2.1/2.2 rules | MPL-2.0 (free) |
| [Playwright](https://playwright.dev) | Headless Chromium | Apache-2.0 (free) |
| Custom heuristics | Lighthouse-style perf/SEO/BP scoring | — |
