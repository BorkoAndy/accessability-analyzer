(function () {
    'use strict';

    const ICON_URL = 'https://andy-a11y-analyzer.vercel.app/MyIcon.png';
    const API_URL  = 'https://andy-a11y-analyzer.vercel.app';
    const API_KEY  = 'Kx9#mP2vN$qL8@wR5yT!';

    // ── Styles (injected once into <head>) ────────────────────────────────────
    function ensureStyles() {
        if (document.getElementById('a11y-analyzer-styles')) return;
        const style = document.createElement('style');
        style.id = 'a11y-analyzer-styles';
        style.textContent = `
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap');

            .a11y-overlay {
                position: fixed;
                inset: 0;
                background: rgba(15, 23, 42, 0.85);
                backdrop-filter: blur(8px);
                z-index: 999999;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Outfit', sans-serif;
                animation: a11y-fade-in 0.2s ease;
            }
            @keyframes a11y-fade-in { from { opacity: 0; } to { opacity: 1; } }

            .a11y-card {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 32px;
                width: 90%;
                max-width: 450px;
                padding: 40px;
                color: #f1f5f9;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,.5);
                position: relative;
                animation: a11y-slide-up 0.25s ease;
            }
            @keyframes a11y-slide-up { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

            .a11y-close {
                position: absolute;
                top: 20px; right: 20px;
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 24px;
                cursor: pointer;
                line-height: 1;
            }
            .a11y-close:hover { color: #fff; }

            .a11y-score-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                margin: 24px 0;
            }
            .a11y-score-box {
                background: #0f172a;
                border: 1px solid #334155;
                padding: 20px;
                border-radius: 20px;
                text-align: center;
            }
            .a11y-score-val {
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 4px;
            }
            .a11y-score-label {
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: .05em;
                color: #94a3b8;
                font-weight: 600;
            }
            .a11y-detail-row {
                display: flex;
                justify-content: space-between;
                padding: 12px 16px;
                background: rgba(59,130,246,.05);
                border-radius: 12px;
                font-size: 14px;
                margin-top: 8px;
            }
            .a11y-btn-full {
                display: block;
                width: 100%;
                background: #3b82f6;
                color: #fff;
                text-align: center;
                padding: 14px;
                border-radius: 14px;
                text-decoration: none;
                font-weight: 600;
                margin-top: 24px;
                transition: background .2s;
            }
            .a11y-btn-full:hover { background: #2563eb; }

            .a11y-loader {
                width: 48px; height: 48px;
                border: 5px solid #334155;
                border-top-color: #3b82f6;
                border-radius: 50%;
                animation: a11y-spin 1s infinite linear;
                margin: 0 auto 24px;
            }
            @keyframes a11y-spin { to { transform: rotate(360deg); } }
        `;
        document.head.appendChild(style);
    }

    // ── Modal: create fresh every time, destroy on close ──────────────────────
    function createModal() {
        const overlay = document.createElement('div');
        overlay.className = 'a11y-overlay';
        overlay.innerHTML = `
            <div class="a11y-card" id="a11y-modal-card">
                <button class="a11y-close" id="a11y-close-btn">&times;</button>

                <!-- Loading State -->
                <div id="a11y-loading">
                    <div style="margin-bottom:24px;text-align:center;">
                        <img src="${ICON_URL}" style="width:60px;height:auto;">
                    </div>
                    <div class="a11y-loader"></div>
                    <h2 style="font-size:20px;margin-bottom:8px;text-align:center;">Analyzing Page…</h2>
                    <p style="color:#94a3b8;font-size:14px;text-align:center;">Running accessibility and performance audits.</p>
                </div>

                <!-- Results State (hidden until done) -->
                <div id="a11y-results" style="display:none;">
                    <div style="margin-bottom:16px;text-align:center;">
                        <img src="${ICON_URL}" style="width:60px;height:auto;">
                    </div>
                    <h2 style="text-align:center;margin-bottom:8px;font-size:22px;">Audit Complete</h2>
                    <p id="a11y-res-url" style="text-align:center;color:#94a3b8;font-size:13px;margin-bottom:24px;word-break:break-all;"></p>

                    <div class="a11y-score-row">
                        <div class="a11y-score-box">
                            <div id="a11y-res-a11y" class="a11y-score-val">--</div>
                            <div class="a11y-score-label">Accessibility</div>
                        </div>
                        <div class="a11y-score-box">
                            <div id="a11y-res-perf" class="a11y-score-val">--</div>
                            <div class="a11y-score-label">Performance</div>
                        </div>
                    </div>

                    <div class="a11y-detail-row">
                        <span style="color:#94a3b8;">Optimization Issues</span>
                        <span id="a11y-res-issues" style="font-weight:600;">--</span>
                    </div>

                    <a id="a11y-res-link" href="#" target="_blank" class="a11y-btn-full">View Detailed Report</a>
                </div>
            </div>
        `;

        // Close on button click or backdrop click
        function closeModal() { overlay.remove(); }
        overlay.querySelector('#a11y-close-btn').addEventListener('click', closeModal);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });

        document.body.appendChild(overlay);
        return overlay;
    }

    function showResults(overlay, data) {
        overlay.querySelector('#a11y-loading').style.display = 'none';
        overlay.querySelector('#a11y-results').style.display = 'block';
        overlay.querySelector('#a11y-close-btn').style.display = '';

        const a11y = data.scores?.accessibility ?? 0;
        const perf = data.scores?.performance ?? 0;
        const errors = data.accessibility?.stats?.errors ?? 0;
        const alerts = data.accessibility?.stats?.alerts ?? 0;

        const a11yEl = overlay.querySelector('#a11y-res-a11y');
        a11yEl.textContent = a11y;
        a11yEl.style.color = a11y >= 90 ? '#10b981' : a11y >= 50 ? '#f59e0b' : '#ef4444';

        const perfEl = overlay.querySelector('#a11y-res-perf');
        perfEl.textContent = perf;
        perfEl.style.color = perf >= 90 ? '#10b981' : perf >= 50 ? '#f59e0b' : '#ef4444';

        overlay.querySelector('#a11y-res-url').textContent = data.url;
        overlay.querySelector('#a11y-res-issues').innerHTML =
            `<span style="color:#ef4444">${errors}</span> / <span style="color:#f59e0b">${alerts}</span>`;
        overlay.querySelector('#a11y-res-link').href =
            `https://andy-a11y-analyzer.vercel.app?url=${encodeURIComponent(data.url)}`;
    }

    // ── Button Injection ───────────────────────────────────────────────────────
    function injectButton() {
        const tlButtons = document.getElementById('tl_buttons');
        if (!tlButtons) return;
        if (document.getElementById('a11y-analyzer-action')) return;

        const btn = document.createElement('a');
        btn.href = '#';
        btn.className = 'header_a11y';
        btn.style.cssText = 'display:inline-block;margin-left:10px;padding:4px 12px;font-size:12px;font-weight:bold;line-height:20px;background:#3b82f6;color:#fff;border-radius:4px;text-decoration:none;vertical-align:middle;cursor:pointer;';
        btn.innerHTML = `<img src="${ICON_URL}" style="height:14px;width:auto;vertical-align:middle;margin-right:5px;"> Analyze Page`;
        btn.title = 'Run an accessibility and performance audit for this page';

        btn.addEventListener('click', async function (e) {
            e.preventDefault();

            const aliasInput = document.querySelector('input[name="alias"]');
            const alias = aliasInput ? aliasInput.value : '';
            const targetUrl = window.location.origin + '/' + alias.replace(/^\//, '');

            console.log('Starting A11y Audit for:', targetUrl);

            // Create fresh modal every time
            ensureStyles();
            const overlay = createModal();
            // Hide close button while loading
            overlay.querySelector('#a11y-close-btn').style.display = 'none';

            try {
                const res = await fetch(`${API_URL}/api/v1/full-audit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
                    body: JSON.stringify({ url: targetUrl })
                });

                if (!res.ok) throw new Error(`API returned ${res.status}: ${res.statusText}`);

                const data = await res.json();
                showResults(overlay, data);

            } catch (err) {
                overlay.remove();
                alert('Analysis failed: ' + err.message);
                console.error(err);
            }
        });

        // Detect Contao version structure and inject
        let targetUl = tlButtons.querySelector('ul[data-contao--operations-menu-target="menu"]')
                     || tlButtons.querySelector('ul');

        if (targetUl) {
            const li = document.createElement('li');
            li.id = 'a11y-analyzer-action';
            li.appendChild(btn);
            targetUl.insertBefore(li, targetUl.children[1] || null);
        } else {
            btn.id = 'a11y-analyzer-action';
            tlButtons.insertBefore(btn, tlButtons.children[1] || null);
        }
    }

    // ── Throttled re-injection to fight Stimulus re-renders ───────────────────
    let reinjectTimer = null;
    function throttledInject() {
        if (reinjectTimer) return;
        reinjectTimer = setTimeout(() => {
            injectButton();
            reinjectTimer = null;
        }, 50);
    }

    // ── Boot ──────────────────────────────────────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => { ensureStyles(); injectButton(); });
    } else {
        ensureStyles();
        injectButton();
    }

    const observer = new MutationObserver(throttledInject);
    observer.observe(document.documentElement, { childList: true, subtree: true });

})();
