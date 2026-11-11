"""Local-only, standard-library demonstration API and static UI for fictional notices."""
from __future__ import annotations
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import argparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data' / 'sample_notices.json'
STATIC = ROOT / 'static'


def load_data() -> dict:
    doc = json.loads(DATA.read_text(encoding='utf-8'))
    if doc['metadata'].get('fictional') is not True or doc['metadata'].get('schema_version') != 2:
        raise ValueError('Expected the fictional v2 dataset. Run python seed.py.')
    if len({item['id'] for item in doc['notices']}) != len(doc['notices']):
        raise ValueError('Duplicate notice IDs')
    return doc


def select(notices: list[dict], *, query='', category='', status='', region='') -> list[dict]:
    query = query.casefold().strip()[:120]
    return [n for n in notices
            if (not query or query in ' '.join((n['title'], n['buyer'], n['id'], n['summary'])).casefold())
            and (not category or n['category'] == category)
            and (not status or n['status'] == status)
            and (not region or n['region'] == region)]


def summary(doc: dict) -> dict:
    items = doc['notices']
    as_of = date.fromisoformat(doc['metadata']['as_of'])
    end = as_of + timedelta(days=14)
    categories = {n['category']: sum(x['category'] == n['category'] for x in items) for n in items}
    return {
        'total': len(items),
        'open': sum(n['status'] in ('Open', 'Amended') for n in items),
        'deadline_14d': sum(n['status'] in ('Open', 'Amended') and n['deadline'] is not None and as_of <= date.fromisoformat(n['deadline']) <= end for n in items),
        'conflicts': sum(n['confidence'] == 'Conflicting source' for n in items),
        'categories': dict(sorted(categories.items(), key=lambda item: (-item[1], item[0]))),
        'as_of': doc['metadata']['as_of'], 'fictional': True,
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, data: bytes, content_type: str, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj, status=200):
        self._send(json.dumps(obj, ensure_ascii=False).encode(), 'application/json; charset=utf-8', status)

    def do_GET(self):
        parsed = urlsplit(self.path)
        path = parsed.path
        if path in ('/', '/static/index.html', '/static/styles.css', '/static/app.js'):
            name = 'index.html' if path == '/' else path.split('/')[-1]
            mime = {'index.html': 'text/html', 'styles.css': 'text/css', 'app.js': 'text/javascript'}[name]
            self._send((STATIC / name).read_bytes(), mime + '; charset=utf-8')
            return
        if path == '/health':
            self._json({'status': 'ok', 'fictional': True})
            return
        doc = load_data()
        if path == '/api/summary':
            self._json(summary(doc)); return
        if path == '/api/notices':
            p = parse_qs(parsed.query, keep_blank_values=False)
            def param(name): return p.get(name, [''])[0][:120]
            items = select(doc['notices'], query=param('query'), category=param('category'), status=param('status'), region=param('region'))
            self._json({'fictional': True, 'count': len(items), 'items': items[:100]}); return
        if path.startswith('/api/notices/'):
            ident = path.removeprefix('/api/notices/')
            item = next((n for n in doc['notices'] if n['id'] == ident), None)
            self._json(item if item else {'error': 'Not found'}, 200 if item else 404); return
        self._json({'error': 'Not found'}, 404)

    def log_message(self, fmt, *args):
        return  # Local demo; do not emit logs containing requests or query strings


def main() -> None:
    ap = argparse.ArgumentParser(description='Fictional procurement demo dashboard (loopback only)')
    ap.add_argument('--port', type=int, default=8768)
    args = ap.parse_args()
    load_data()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'FICTIONAL procurement dashboard: http://127.0.0.1:{args.port} (Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
