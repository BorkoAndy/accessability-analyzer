import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import tldextract

class handler:
    @staticmethod
    def extract_main_domain(url):
        ext = tldextract.extract(url)
        return f"{ext.domain}.{ext.suffix}"

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
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"error": "URL required"}')
            return

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            
            # Use TLD extract to get the "root" domain of the input URL
            input_domain = handler.extract_main_domain(url)
            
            all_links = set()
            sitemaps_found = []

            # ── 1. XML DISCOVERY ──
            parsed_input = urlparse(url)
            base_input = f"{parsed_input.scheme}://{parsed_input.netloc}"
            
            common_xml = ["/robots.txt", "/sitemap.xml", "/sitemap_index.xml", "/share/sitemap.xml"]
            for path in common_xml:
                test_url = urljoin(base_input, path)
                try:
                    r = requests.get(test_url, timeout=5, headers=headers)
                    if r.status_code == 200:
                        if path == "/robots.txt":
                            for line in r.text.splitlines():
                                if line.lower().startswith("sitemap:"):
                                    sm_path = line.split(":", 1)[1].strip()
                                    if sm_path not in sitemaps_found: sitemaps_found.append(sm_path)
                        else:
                            if test_url not in sitemaps_found: sitemaps_found.append(test_url)
                except: continue

            # Parse XML Sitemaps
            for s_url in sitemaps_found:
                try:
                    resp = requests.get(s_url, timeout=8, headers=headers)
                    if resp.status_code == 200:
                        try: soup = BeautifulSoup(resp.content, "xml")
                        except: soup = BeautifulSoup(resp.content, "html.parser")
                        for loc in soup.find_all("loc"):
                            all_links.add(loc.text)
                except: continue

            # ── 2. FAILSAFE CRAWLER ──
            if not all_links:
                r_home = requests.get(url, timeout=10, headers=headers)
                if r_home.status_code == 200:
                    # IMPORTANT: Use the FINAL URL after redirects for all resolution!
                    final_url = r_home.url
                    final_domain = handler.extract_main_domain(final_url)
                    h_soup = BeautifulSoup(r_home.content, "html.parser")

                    # A. HTML Sitemap Link
                    sm_candidates = h_soup.find_all('a', href=True, text=re.compile(r'sitemap', re.I))
                    sm_candidates += h_soup.find_all('a', href=re.compile(r'sitemap', re.I))
                    
                    for a in sm_candidates:
                        sm_url = urljoin(final_url, a['href'])
                        try:
                            r_sm = requests.get(sm_url, timeout=5, headers=headers)
                            if r_sm.status_code == 200:
                                sm_soup = BeautifulSoup(r_sm.content, "html.parser")
                                for a_nav in sm_soup.find_all('a', href=True):
                                    link = urljoin(sm_url, a_nav['href'])
                                    if handler.extract_main_domain(link) in [input_domain, final_domain]:
                                        all_links.add(link)
                                break 
                        except: continue

                    # B. Navigation & General Links
                    if not all_links:
                        # Prioritize <nav> tags as per user request
                        nav_tags = h_soup.find_all(['nav', 'header', 'footer'])
                        target_tags = nav_tags if nav_tags else [h_soup]
                        
                        for container in target_tags:
                            for a in container.find_all('a', href=True):
                                link = urljoin(final_url, a['href'])
                                # Extract parts to ignore anchors/parameters
                                clean_url = link.split('#')[0].split('?')[0].rstrip('/')
                                
                                # Check if it's the same main domain (avoiding external noise)
                                if handler.extract_main_domain(clean_url) in [input_domain, final_domain]:
                                    # Avoid including the landing page itself
                                    if clean_url != final_url.rstrip('/'):
                                        all_links.add(clean_link if 'clean_link' in locals() else clean_url)

            # Cleanup
            junk = ('.xml', '.pdf', '.jpg', '.png', '.zip', '.docx', '.js', '.css')
            results = sorted([u for u in all_links if not u.lower().endswith(junk)])

            response_data = {
                "count": len(results),
                "urls": results[:800] 
            }

            body = json.dumps(response_data).encode()
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
