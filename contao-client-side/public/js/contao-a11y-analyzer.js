(function () {
    'use strict';

    console.log('A11y Analyzer Contao Client Loaded');

    function init() {
        // Use MutationObserver for dynamic backend elements
        const observer = new MutationObserver(() => injectButton());
        observer.observe(document.body, { childList: true, subtree: true });
        injectButton();
    }

    function injectButton() {
        const tlButtons = document.getElementById('tl_buttons');
        if (!tlButtons) return;

        const ul = tlButtons.querySelector('ul');
        if (!ul) return;

        // If the button is already perfectly in place, do nothing. 
        // This solves the issue of Contao rewriting the HTML and blowing away our button.
        if (document.getElementById('a11y-analyzer-action')) return;

        const li = document.createElement('li');
        li.id = 'a11y-analyzer-action';
        
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
        btn.innerHTML = '♿ Analyze Page';
        btn.title = 'Run an accessibility and performance audit for this page';

        btn.addEventListener('click', async function(e) {
            e.preventDefault();

            // 1. Determine URL to analyze
            let alias = '';
            const aliasInput = document.querySelector('input[name="alias"]');
            if (aliasInput && aliasInput.value) {
                alias = aliasInput.value;
            }
            
            // Ask user to confirm or provide full URL
            let defaultBase = window.location.origin + '/';
            let storedBase = localStorage.getItem('a11y_base_url') || defaultBase;
            
            let targetUrl = prompt("Enter the exact frontend URL to analyze:", storedBase + alias);
            if (!targetUrl) return;

            // Save the base part for future use
            try {
                let u = new URL(targetUrl);
                localStorage.setItem('a11y_base_url', u.origin + '/');
            } catch(e) {}

            // 2. Get API connection details
            let apiUrl = localStorage.getItem('a11y_api_url') || 'https://your-vercel-app.vercel.app';
            apiUrl = prompt("Enter A11y API URL:", apiUrl);
            if (!apiUrl) return;
            localStorage.setItem('a11y_api_url', apiUrl);

            let apiKey = localStorage.getItem('analyze_pass') || '';
            apiKey = prompt("Enter API Password:", apiKey);
            if (!apiKey) return;
            localStorage.setItem('analyze_pass', apiKey);

            console.log('Starting A11y Audit for:', targetUrl);
            btn.innerHTML = '⌛ Analyzing... (This takes about ~10s)';
            btn.disabled = true;

            // Remove old results if exist
            const oldRes = document.querySelector('.a11y-results-panel');
            if (oldRes) oldRes.remove();

            try {
                const res = await fetch(`${apiUrl.replace(/\/$/, '')}/api/v1/full-audit`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': apiKey
                    },
                    body: JSON.stringify({ url: targetUrl })
                });

                if (!res.ok) {
                    if (res.status === 401) {
                        localStorage.removeItem('analyze_pass');
                        throw new Error('Unauthorized - Invalid Password');
                    }
                    throw new Error(`API returned ${res.status}`);
                }

                const data = await res.json();
                
                // 3. Render Results Panel right below the tl_buttons
                renderResultsPanel(tlButtons, data);

            } catch (err) {
                alert('Analysis failed: ' + err.message);
                console.error(err);
            } finally {
                btn.innerHTML = '♿ Analyze Page';
                btn.disabled = false;
            }
        });

        li.appendChild(btn);

        // Insert after the first child (usually "Go back")
        if (ul.children.length > 0) {
            ul.insertBefore(li, ul.children[1]);
        } else {
            ul.appendChild(li);
        }
    }

    function renderResultsPanel(tlButtons, data) {
        const panel = document.createElement('div');
        panel.className = 'a11y-results-panel';
        panel.style.marginTop = '15px';
        panel.style.padding = '15px';
        panel.style.backgroundColor = '#f8fafc';
        panel.style.border = '1px solid #cbd5e1';
        panel.style.borderRadius = '8px';
        panel.style.fontFamily = 'sans-serif';
        
        const a11yScore = data.scores.accessibility ?? 0;
        const perfScore = data.scores.performance ?? 0;
        const errors = data.accessibility?.stats?.errors ?? 0;
        const alerts = data.accessibility?.stats?.alerts ?? 0;

        const getScoreColor = (score) => {
            if (score >= 90) return '#10b981'; // Green
            if (score >= 50) return '#f59e0b'; // Orange
            return '#ef4444'; // Red
        };

        panel.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                📊 A11y & Performance Audit Results
            </div>
            <div style="display: flex; gap: 20px; font-size: 14px;">
                <div style="flex: 1; background: #fff; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: ${getScoreColor(a11yScore)}">${a11yScore}</div>
                    <div style="color: #64748b; font-size: 11px; text-transform: uppercase;">Accessibility</div>
                </div>
                <div style="flex: 1; background: #fff; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: ${getScoreColor(perfScore)}">${perfScore}</div>
                    <div style="color: #64748b; font-size: 11px; text-transform: uppercase;">Performance</div>
                </div>
                <div style="flex: 2; background: #fff; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
                    <div style="margin-bottom: 4px;"><strong>Issues:</strong> <span style="color: #ef4444">${errors} Errors</span>, <span style="color: #f59e0b">${alerts} Alerts</span></div>
                    <div style="font-size: 12px; color: #64748b;">${data.url}</div>
                    <div style="font-size: 11px; margin-top: 6px;">
                        <a href="${localStorage.getItem('a11y_api_url') || '#'}" target="_blank" style="color: #3b82f6; text-decoration: none;">View Full Report in Analyzer App →</a>
                    </div>
                </div>
            </div>
        `;
        // Insert right after the tl_buttons container
        tlButtons.parentNode.insertBefore(panel, tlButtons.nextSibling);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
