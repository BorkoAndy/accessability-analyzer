(function () {
    'use strict';

    function init() {
        // 1. Inject Styles for the Tool-Style Modal
        if (!document.getElementById('a11y-analyzer-styles')) {
            const style = document.createElement('style');
            style.id = 'a11y-analyzer-styles';
            style.innerHTML = `
                @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap');
                
                #a11y-modal-overlay {
                    position: fixed;
                    inset: 0;
                    background: rgba(15, 23, 42, 0.85);
                    backdrop-filter: blur(8px);
                    z-index: 999999;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-family: 'Outfit', sans-serif;
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 0.3s ease;
                }
                #a11y-modal-overlay.active {
                    opacity: 1;
                    pointer-events: auto;
                }
                .a11y-modal-card {
                    background: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 32px;
                    width: 90%;
                    max-width: 450px;
                    padding: 40px;
                    color: #f1f5f9;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                    transform: translateY(20px);
                    transition: transform 0.3s ease;
                    position: relative;
                }
                #a11y-modal-overlay.active .a11y-modal-card {
                    transform: translateY(0);
                }
                .a11y-modal-close {
                    position: absolute;
                    top: 20px;
                    right: 20px;
                    background: transparent;
                    border: none;
                    color: #94a3b8;
                    font-size: 24px;
                    cursor: pointer;
                    line-height: 1;
                }
                .a11y-modal-close:hover { color: #fff; }
                
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
                    letter-spacing: 0.05em;
                    color: #94a3b8;
                    font-weight: 600;
                }
                .a11y-detail-row {
                    display: flex;
                    justify-content: space-between;
                    padding: 12px 16px;
                    background: rgba(59, 130, 246, 0.05);
                    border-radius: 12px;
                    font-size: 14px;
                    margin-top: 8px;
                }
                .a11y-btn-full {
                    display: block;
                    width: 100%;
                    background: #3b82f6;
                    color: white;
                    text-align: center;
                    padding: 14px;
                    border-radius: 14px;
                    text-decoration: none;
                    font-weight: 600;
                    margin-top: 24px;
                    transition: background 0.2s;
                }
                .a11y-btn-full:hover { background: #2563eb; }

                /* Loader Animation */
                .a11y-loader {
                    width: 48px;
                    height: 48px;
                    border: 5px solid #334155;
                    border-top-color: #3b82f6;
                    border-radius: 50%;
                    animation: a11y-spin 1s infinite linear;
                    margin: 0 auto 24px;
                }
                @keyframes a11y-spin { to { transform: rotate(360deg); } }
                
                .a11y-loading-state { display: none; text-align: center; padding: 20px 0; }
                .a11y-results-state { display: block; }
                
                .a11y-modal-card.is-loading .a11y-loading-state { display: block; }
                .a11y-modal-card.is-loading .a11y-results-state { display: none; }
                .a11y-modal-card.is-loading .a11y-modal-close { display: none; }
            `;
            document.head.appendChild(style);
        }

        // 2. Create the Modal element
        if (!document.getElementById('a11y-modal-overlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'a11y-modal-overlay';
            overlay.innerHTML = `
                <div class="a11y-modal-card" id="a11y-modal-card">
                    <button class="a11y-modal-close" onclick="document.getElementById('a11y-modal-overlay').classList.remove('active')">&times;</button>
                    
                    <!-- Loading State -->
                    <div class="a11y-loading-state">
                        <div style="margin-bottom: 24px; text-align: center;">
                            <img src="https://andy-a11y-analyzer.vercel.app/MyIcon.png" style="width: 60px; height: auto;">
                        </div>
                        <div class="a11y-loader"></div>
                        <h2 style="font-size: 20px; margin-bottom: 8px;">Analyzing Page...</h2>
                        <p style="color: #94a3b8; font-size: 14px;">Running accessibility and performance audits.</p>
                    </div>

                    <!-- Results State -->
                    <div class="a11y-results-state">
                        <div style="margin-bottom: 16px; text-align: center;">
                            <img src="https://andy-a11y-analyzer.vercel.app/MyIcon.png" style="width: 60px; height: auto;">
                        </div>
                        <h2 style="text-align: center; margin-bottom: 8px; font-size: 22px;">Audit Complete</h2>
                        <p id="a11y-modal-url" style="text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 24px; word-break: break-all;"></p>
                        
                        <div class="a11y-score-row">
                            <div class="a11y-score-box">
                                <div id="a11y-score-val-a11y" class="a11y-score-val">--</div>
                                <div class="a11y-score-label">Accessibility</div>
                            </div>
                            <div class="a11y-score-box">
                                <div id="a11y-score-val-perf" class="a11y-score-val">--</div>
                                <div class="a11y-score-label">Performance</div>
                            </div>
                        </div>

                        <div class="a11y-detail-row">
                            <span style="color: #94a3b8">Optimization Issues</span>
                            <span id="a11y-modal-issues" style="font-weight: 600;">--</span>
                        </div>

                        <a id="a11y-modal-link" href="#" target="_blank" class="a11y-btn-full">View Detailed Report</a>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
        }

        // Use MutationObserver for dynamic backend elements
        const observer = new MutationObserver(() => injectButton());
        observer.observe(document.body, { childList: true, subtree: true });
        injectButton();
    }

    function showResultModal(data, isLoading = false) {
        const overlay = document.getElementById('a11y-modal-overlay');
        const card = document.getElementById('a11y-modal-card');

        if (isLoading) {
            card.classList.add('is-loading');
            overlay.classList.add('active');
            return;
        }

        card.classList.remove('is-loading');

        const a11yScore = data.scores.accessibility ?? 0;
        const perfScore = data.scores.performance ?? 0;
        const errors = data.accessibility?.stats?.errors ?? 0;
        const alerts = data.accessibility?.stats?.alerts ?? 0;

        document.getElementById('a11y-modal-url').textContent = data.url;

        const a11yEl = document.getElementById('a11y-score-val-a11y');
        a11yEl.textContent = a11yScore;
        a11yEl.style.color = a11yScore >= 90 ? '#10b981' : (a11yScore >= 50 ? '#f59e0b' : '#ef4444');

        const perfEl = document.getElementById('a11y-score-val-perf');
        perfEl.textContent = perfScore;
        perfEl.style.color = perfScore >= 90 ? '#10b981' : (perfScore >= 50 ? '#f59e0b' : '#ef4444');

        document.getElementById('a11y-modal-issues').innerHTML =
            `<span style="color:#ef4444">${errors}</span> / <span style="color:#f59e0b">${alerts}</span>`;

        document.getElementById('a11y-modal-link').href = `https://andy-a11y-analyzer.vercel.app?url=${encodeURIComponent(data.url)}`;

        overlay.classList.add('active');
    }

    function injectButton() {
        const tlButtons = document.getElementById('tl_buttons');
        if (!tlButtons) return;

        // If the button is already perfectly in place, do nothing. 
        // This solves the issue of Contao rewriting the HTML and blowing away our button.
        if (document.getElementById('a11y-analyzer-action')) return;

        // Create the button as an anchor tag to fit the header nicely
        const btn = document.createElement('a');
        btn.href = '#';
        btn.className = 'header_a11y';
        btn.style.display = 'inline-block';
        btn.style.marginLeft = '10px';
        btn.style.padding = '4px 12px';
        btn.style.fontSize = '12px';
        btn.style.fontWeight = 'bold';
        btn.style.lineHeight = '20px';
        btn.style.backgroundColor = '#3b82f6';
        btn.style.color = '#fff';
        btn.style.borderRadius = '4px';
        btn.style.textDecoration = 'none';
        btn.style.verticalAlign = 'middle';
        const iconUrl = 'https://andy-a11y-analyzer.vercel.app/MyIcon.png';
        btn.innerHTML = `<img src="${iconUrl}" style="height:14px; width:auto; vertical-align:middle; margin-right:5px;"> Analyze Page`;
        btn.title = 'Run an accessibility and performance audit for this page';

        btn.addEventListener('click', async function (e) {
            e.preventDefault();

            // 1. Determine URL to analyze automatically
            const aliasInput = document.querySelector('input[name="alias"]');
            const alias = aliasInput ? aliasInput.value : '';

            // Construct target URL using current browser origin
            const base = window.location.origin;
            const targetUrl = base + '/' + alias.replace(/^\//, '');

            // 2. Hardcoded API connection details
            const apiUrl = 'https://andy-a11y-analyzer.vercel.app';
            const apiKey = 'Kx9#mP2vN$qL8@wR5yT!';

            console.log('Starting A11y Audit for:', targetUrl);

            // Show modal immediately in loading state
            showResultModal(null, true);

            try {
                const res = await fetch(`${apiUrl}/api/v1/full-audit`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': apiKey
                    },
                    body: JSON.stringify({ url: targetUrl })
                });

                if (!res.ok) {
                    throw new Error(`API returned ${res.status}: ${res.statusText}`);
                }

                const data = await res.json();

                // 3. Update modal with final results
                showResultModal(data);

            } catch (err) {
                // If failed, close modal and show alert
                document.getElementById('a11y-modal-overlay').classList.remove('active');
                alert('Analysis failed: ' + err.message);
                console.error(err);
            }
        });

        // Smart Injection: Detect Contao Version Structure
        const ul = tlButtons.querySelector('ul');

        if (ul) {
            // Contao 5.7+ (ul/li operations submenu structure)
            const li = document.createElement('li');
            li.id = 'a11y-analyzer-action';
            li.appendChild(btn);

            if (ul.children.length > 0) {
                ul.insertBefore(li, ul.children[1]);
            } else {
                ul.appendChild(li);
            }
        } else {
            // Contao < 5.7 (Flat anchors directly inside #tl_buttons)
            btn.id = 'a11y-analyzer-action';

            if (tlButtons.children.length > 0) {
                // Insert directly after the first element (usually "Go back")
                const nextEl = tlButtons.children[1] || null;
                tlButtons.insertBefore(btn, nextEl);
            } else {
                tlButtons.appendChild(btn);
            }
        }

        // Fallback for Contao 5.7 variants where 'ul' might not be a direct child
        if (!ul && tlButtons.querySelector('.tl_buttons_toolbar ul')) {
            const innerUl = tlButtons.querySelector('.tl_buttons_toolbar ul');
            const li = document.createElement('li');
            li.id = 'a11y-analyzer-action';
            li.appendChild(btn);
            innerUl.insertBefore(li, innerUl.children[1] || null);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
