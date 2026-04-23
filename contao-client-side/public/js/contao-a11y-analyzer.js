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
        btn.innerHTML = '♿ Analyze Page';
        btn.title = 'Run an accessibility and performance audit for this page';

        btn.addEventListener('click', async function(e) {
            e.preventDefault();

            // 1. Determine URL to analyze automatically
            const aliasInput = document.querySelector('input[name="alias"]');
            const alias = aliasInput ? aliasInput.value : '';
            
            // Construct target URL using current browser origin
            const targetUrl = window.location.origin + '/' + alias;

            // 2. Hardcoded API connection details
            const apiUrl = 'https://andy-a11y-analyzer.vercel.app';
            const apiKey = 'Kx9#mP2vN$qL8@wR5yT!';

            console.log('Starting A11y Audit for:', targetUrl);
            const originalText = btn.innerHTML;
            btn.innerHTML = '⌛ Analyzing...';
            btn.style.opacity = '0.7';
            btn.style.pointerEvents = 'none';

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
                
                // 3. Display Results via Alert Window
                const a11yScore = data.scores.accessibility ?? 0;
                const perfScore = data.scores.performance ?? 0;
                const errors = data.accessibility?.stats?.errors ?? 0;
                const alerts = data.accessibility?.stats?.alerts ?? 0;

                alert(
                    `📊 Audit Results for ${data.url}\n\n` +
                    `✅ Accessibility Score: ${a11yScore}/100\n` +
                    `⚡ Performance Score: ${perfScore}/100\n\n` +
                    `⚠️ Issues: ${errors} Errors, ${alerts} Alerts\n\n` +
                    `Full report available at the Analyzer App.`
                );

            } catch (err) {
                alert('Analysis failed: ' + err.message);
                console.error(err);
            } finally {
                btn.innerHTML = originalText;
                btn.style.opacity = '1';
                btn.style.pointerEvents = 'auto';
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
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
