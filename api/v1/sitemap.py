import json
import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urljoin

class handler:
    @staticmethod
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data)
            url = data.get('url') # Can be homepage or sitemap URL
        except:
            url = None

        if not url:
            self.send_response(400)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"error": "URL required"}')
            return

        try:
            # 1. Discovery Logic
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            sitemap_urls = []
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

            # A. Manual Robots.txt search (more reliable than urllib)
            try:
                r_robots = requests.get(urljoin(base_url, "/robots.txt"), timeout=5, headers=headers)
                if r_robots.status_code == 200:
                    for line in r_robots.text.splitlines():
                        if line.lower().startswith("sitemap:"):
                            s_path = line.split(":", 1)[1].strip()
                            if s_path not in sitemap_urls: sitemap_urls.append(s_path)
            except:
                pass

            # B. Check Homepage HTML for <link rel="sitemap">
            try:
                r_home = requests.get(base_url, timeout=5, headers=headers)
                if r_home.status_code == 200:
                    h_soup = BeautifulSoup(r_home.content, "html.parser")
                    sm_link = h_soup.find("link", attrs={"rel": "sitemap"})
                    if sm_link and sm_link.get("href"):
                        href = urljoin(base_url, sm_link.get("href"))
                        if href not in sitemap_urls: sitemap_urls.append(href)
            except:
                pass

            # C. If still empty, try direct URL (if it looks like a sitemap)
            if not sitemap_urls and url.endswith('.xml'):
                sitemap_urls.append(url)

            # D. Brute force common locations (Extended)
            common_paths = [
                "/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml",
                "/share/sitemap.xml", "/page-sitemap.xml", "/post-sitemap.xml",
                "/sitemaps/sitemap.xml", "/sitemap/sitemap.xml", "/en/sitemap.xml"
            ]
            for path in common_paths:
                test_url = urljoin(base_url, path)
                try:
                    r = requests.head(test_url, timeout=3, headers=headers)
                    if r.status_code == 200:
                        if test_url not in sitemap_urls: sitemap_urls.append(test_url)
                        # We don't break here, we collect all valid ones
                except:
                    continue

            # 2. Parsing Logic (Recursive)
            all_discovered_links = set()
            
            for s_url in sitemap_urls:
                try:
                    resp = requests.get(s_url, timeout=10, headers=headers)
                    if resp.status_code == 200:
                        try:
                            soup = BeautifulSoup(resp.content, "xml")
                        except:
                            soup = BeautifulSoup(resp.content, "html.parser")
                        
                        # Handle Sitemap Index
                        sitemaps = soup.find_all("sitemap")
                        for sm in sitemaps:
                            loc = sm.find("loc")
                            if loc:
                                try:
                                    nested_resp = requests.get(loc.text, timeout=8, headers=headers)
                                    if nested_resp.status_code == 200:
                                        try:
                                            nested_soup = BeautifulSoup(nested_resp.content, "xml")
                                        except:
                                            nested_soup = BeautifulSoup(nested_resp.content, "html.parser")
                                        for loc_tag in nested_soup.find_all("loc"):
                                            all_discovered_links.add(loc_tag.text)
                                except:
                                    continue
                        
                        # Handle standard Sitemap URLs
                        for loc_tag in soup.find_all("loc"):
                            all_discovered_links.add(loc_tag.text)
                except:
                    continue

            # Cleanup: filter out XML files and normalize
            final_urls = sorted([u for u in all_discovered_links if not u.lower().endswith('.xml')])
            
            response_data = {
                "sitemaps_found": sitemap_urls,
                "count": len(final_urls),
                "urls": final_urls[:800] # Increased limit for large sites
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
