import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re

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
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"error": "URL required"}')
            return

        try:
            # ── 1. XML DISCOVERY (Phase 1) ──
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            sitemap_xml_urls = []

            # Robots.txt
            try:
                r_robots = requests.get(urljoin(base_url, "/robots.txt"), timeout=5, headers=headers)
                if r_robots.status_code == 200:
                    for line in r_robots.text.splitlines():
                        if line.lower().startswith("sitemap:"):
                            s_path = line.split(":", 1)[1].strip()
                            if s_path not in sitemap_xml_urls: sitemap_xml_urls.append(s_path)
            except: pass

            # Brute force common XML paths
            common_xml = ["/sitemap.xml", "/sitemap_index.xml", "/share/sitemap.xml", "/sitemap-index.xml"]
            for path in common_xml:
                test_url = urljoin(base_url, path)
                try:
                    r = requests.head(test_url, timeout=3, headers=headers)
                    if r.status_code == 200 and test_url not in sitemap_xml_urls:
                        sitemap_xml_urls.append(test_url)
                except: continue

            # ── 2. EXTRACTION logic ──
            all_links = set()

            # Process XML Sitemaps
            for s_url in sitemap_xml_urls:
                try:
                    resp = requests.get(s_url, timeout=8, headers=headers)
                    if resp.status_code == 200:
                        try: soup = BeautifulSoup(resp.content, "xml")
                        except: soup = BeautifulSoup(resp.content, "html.parser")
                        for loc in soup.find_all("loc"):
                            all_links.add(loc.text)
                except: continue

            # ── 3. FAILSAFE CRAWLER (Phase 2) ──
            if not all_links:
                try:
                    r_home = requests.get(base_url, timeout=8, headers=headers)
                    if r_home.status_code == 200:
                        h_soup = BeautifulSoup(r_home.content, "html.parser")
                        
                        # A. Search for HTML Sitemap links (sitemap.htm, sitemap.php, etc)
                        # or links containing the word 'sitemap'
                        sitemap_candidates = h_soup.find_all('a', href=True, text=re.compile(r'sitemap', re.I))
                        sitemap_candidates += h_soup.find_all('a', href=re.compile(r'sitemap', re.I))
                        
                        found_html_sm = False
                        for a in sitemap_candidates:
                            sm_url = urljoin(base_url, a['href'])
                            if sm_url != base_url: # Avoid infinitely hitting homepage
                                try:
                                    r_sm = requests.get(sm_url, timeout=5, headers=headers)
                                    if r_sm.status_code == 200:
                                        sm_soup = BeautifulSoup(r_sm.content, "html.parser")
                                        for a_nav in sm_soup.find_all('a', href=True):
                                            link = urljoin(base_url, a_nav['href'])
                                            if urlparse(link).netloc == urlparse(base_url).netloc:
                                                all_links.add(link)
                                        found_html_sm = True
                                        break # Found a good HTML sitemap
                                except: continue
                        
                        # B. Navigation Scraper (If still nothing, just grab all internal homepage links)
                        if not found_html_sm:
                            for a in h_soup.find_all('a', href=True):
                                link = urljoin(base_url, a['href'])
                                # Must be same domain and not the homepage itself / anchors
                                if urlparse(link).netloc == urlparse(base_url).netloc:
                                    clean_link = link.split('#')[0].split('?')[0].rstrip('/')
                                    if clean_link and clean_link != base_url.rstrip('/'):
                                        all_links.add(clean_link)
                except: pass

            # ── 4. CLEANUP & RESPONSE ──
            # Filter out assets and non-page files
            junk = ('.xml', '.pdf', '.jpg', '.png', '.zip', '.docx', '.js', '.css')
            final_urls = sorted([u for u in all_links if not u.lower().endswith(junk)])

            response_data = {
                "method": "discovery" if sitemap_xml_urls else "crawling",
                "count": len(final_urls),
                "urls": final_urls[:500] 
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
