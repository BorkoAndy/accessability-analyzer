import json
import time

# Internal imports from sibling files
import api.v1.analyze as analyze
import api.v1.lighthouse as lighthouse

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

        # Auto-prepend https:// if missing (same as sitemap.py fix)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            # Run both audits
            start_time = time.time()
            a_results = analyze.Logic.run_audit(url)
            l_results = lighthouse.Logic.run_audit(url)
            total_time = time.time() - start_time

            # Merge results for a master API response
            response_data = {
                "url": a_results.get('url', url),
                "timestamp": int(time.time()),
                "duration": round(total_time, 2),
                "scores": {
                    "accessibility": a_results['score'],
                    "performance": l_results['scores']['performance'],
                    "bestPractices": l_results['scores']['bestPractices'],
                    "seo": l_results['scores']['seo']
                },
                "accessibility": {
                    "stats": a_results['stats'],
                    "issues": a_results['issues']
                },
                "performance_details": {
                    "audits": l_results['audits']
                }
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
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
