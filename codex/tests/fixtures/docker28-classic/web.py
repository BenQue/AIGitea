"""Synthetic Issue #296 web fixture; only loopback-in-container HTTP health."""
import http.server
import pathlib
import sys
import urllib.request

if len(sys.argv) > 1 and sys.argv[1] == 'healthcheck':
    with urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2) as response:
        raise SystemExit(0 if response.status == 200 else 1)


class Health(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(503 if pathlib.Path('/fixture-fail').exists() else 200)
        self.end_headers()
        self.wfile.write(b'issue296 synthetic health\n')

    def log_message(self, *_):
        pass


http.server.HTTPServer(('0.0.0.0', 8080), Health).serve_forever()
