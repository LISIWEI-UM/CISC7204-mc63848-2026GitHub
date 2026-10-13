"""Serve CARTO tiles locally without embedding the private API key in notebooks."""
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import re
import requests

ROOT = Path(__file__).resolve().parent
KEY = (ROOT / '.runtime/carto_api_key.txt').read_text(encoding='utf-8').strip()

class Tiles(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        match = re.fullmatch(r'/carto/(light_all|dark_all)/(\d{1,2})/(\d+)/(\d+)\.png', self.path)
        if not match:
            self.send_error(404); return
        style, zoom, x, y = match.groups()
        if int(zoom) > 20 or int(x) >= 2**int(zoom) or int(y) >= 2**int(zoom):
            self.send_error(400); return
        try:
            response = requests.get(
                f'https://basemaps.cartocdn.com/{style}/{zoom}/{x}/{y}.png',
                params={'key': KEY}, timeout=20)
            response.raise_for_status()
            if not response.headers.get('Content-Type', '').startswith('image/'):
                raise ValueError('Unexpected tile response')
            self.send_response(200)
            self.send_header('Content-Type', response.headers['Content-Type'])
            self.send_header('Content-Length', str(len(response.content)))
            self.send_header('Cache-Control', 'private, max-age=3600')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.content)
        except Exception:
            self.send_error(502, 'Basemap tile unavailable')

if __name__ == '__main__':
    print('Local CARTO tiles: http://127.0.0.1:8894 (key remains private)', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8894), Tiles).serve_forever()
