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

            # A. Check robots.txt
            try:
                rp = RobotFileParser()
                rp.set_url(urljoin(base_url, "/robots.txt"))
                rp.read()
                found_sitemaps = rp.site_maps()
                if found_sitemaps:
                    sitemap_urls.extend(found_sitemaps)
            except:
                pass

            # B. If robots.txt search failed or URL looks like a direct sitemap, try the URL itself
            if not sitemap_urls:
                if url.endswith('.xml'):
                    sitemap_urls.append(url)
                else:
                    # C. Brute force common locations
                    common_paths = ["/sitemap.xml", "/sitemap_index.xml", "/sitemaps/sitemap.xml"]
                    for path in common_paths:
                        test_url = urljoin(base_url, path)
                        try:
                            # Just check if it exists and is XML
                            r = requests.head(test_url, timeout=3)
                            if r.status_code == 200:
                                sitemap_urls.append(test_url)
                                break
                        except:
                            continue

            # 2. Parsing Logic
            all_discovered_links = set()
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            
            for s_url in sitemap_urls:
                try:
                    resp = requests.get(s_url, timeout=10, headers=headers)
                    if resp.status_code == 200:
                        # Use 'xml' parser (lxml) for better accuracy, fallback to html.parser if needed
                        try:
                            soup = BeautifulSoup(resp.content, "xml")
                        except:
                            soup = BeautifulSoup(resp.content, "html.parser")
                        
                        # Handle Sitemap Index (contains other sitemaps)
                        sitemaps = soup.find_all("sitemap")
                        if sitemaps:
                            for sm in sitemaps:
                                loc = sm.find("loc")
                                if loc:
                                    # Follow nested sitemap
                                    nested_resp = requests.get(loc.text, timeout=5, headers=headers)
                                    if nested_resp.status_code == 200:
                                        try:
                                            nested_soup = BeautifulSoup(nested_resp.content, "xml")
                                        except:
                                            nested_soup = BeautifulSoup(nested_resp.content, "html.parser")
                                        for loc_tag in nested_soup.find_all("loc"):
                                            all_discovered_links.add(loc_tag.text)
                        
                        # Handle standard Sitemap
                        for loc_tag in soup.find_all("loc"):
                            # Filter out non-page URLs if they come from the <sitemap> tag logic above
                            all_discovered_links.add(loc_tag.text)
                except:
                    continue

            # Filter out URLs that are actually other sitemaps (standard in sitemap index files)
            final_urls = [u for u in all_discovered_links if not u.endswith('.xml')]
            
            response_data = {
                "sitemaps_found": sitemap_urls,
                "count": len(final_urls),
                "urls": sorted(list(final_urls))[:500] # Cap at 500 for UI stability
            }

            body = json.dumps(response_data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
