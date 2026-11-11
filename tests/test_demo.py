import json
import unittest
from datetime import date
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import load_data, select, summary, Handler
from seed import generate

class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.doc=load_data()

    def test_dataset_is_fictional(self):
        self.assertTrue(self.doc['metadata']['fictional'])
        self.assertEqual(self.doc['metadata']['as_of'], '2026-11-11')
        self.assertEqual(self.doc, generate())
    def test_unique_ids_and_schema(self):
        items=self.doc['notices'];self.assertEqual(len(items),len({x['id'] for x in items}))
        for n in items:
            self.assertEqual(n['eligibility'], 'Not assessed')
            if n['deadline'] is not None:
                self.assertIsInstance(date.fromisoformat(n['deadline']), date)
    def test_search_and_filter(self):
        items=self.doc['notices']
        found=select(items, query='DATA', category='Data & BI', status='Open')
        self.assertTrue(found)
        self.assertTrue(all(n['category']=='Data & BI' and n['status']=='Open' for n in found))
        self.assertFalse(select(items, query='impossible made up keyword'))
        self.assertEqual(len(select(items)),len(items))
    def test_conflicting_sources_are_not_silently_resolved(self):
        flagged=[x for x in self.doc['notices'] if x['confidence']=='Conflicting source']
        self.assertEqual(len(flagged),3)
        for notice in flagged:
            self.assertIsNone(notice['deadline'])
            self.assertTrue(any(h['event'] == 'Data conflict' for h in notice['history']))
            evidence = notice['deadline_evidence']
            self.assertEqual(len({item['deadline'] for item in evidence}), 2)
            self.assertEqual(len({item['source'] for item in evidence}), 2)
            for item in evidence:
                self.assertLess(date.fromisoformat(item['observed']), date.fromisoformat(item['deadline']))

    def test_disputed_notice_excluded_from_due_count(self):
        disputed = next(n for n in self.doc['notices'] if n['deadline_evidence'])
        self.assertEqual(summary(self.doc)['deadline_14d'], 4)
        earlier = disputed['deadline_evidence'][0]['deadline']
        promoted = {**disputed, 'deadline': earlier}
        changed = {**self.doc, 'notices': [promoted if n is disputed else n for n in self.doc['notices']]}
        self.assertEqual(summary(changed)['deadline_14d'], 5)
    def test_summary_consistency(self):
        m=summary(self.doc)
        self.assertEqual(sum(m['categories'].values()),m['total'])
        self.assertEqual(m['conflicts'],3)
        self.assertEqual(m['fictional'],True)
    def test_no_external_asset_or_outbound_form(self):
        root=Path(__file__).resolve().parents[1]/'static'
        html=(root/'index.html').read_text()
        self.assertNotIn('http://',' '.join(html.split('href=')[1:]))
        self.assertNotIn('<form',html)
        js=(root/'app.js').read_text()
        self.assertNotIn('innerHTML',js)
class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_conflicting_notice_and_headers(self):
        with urlopen(self.base_url + '/api/notices/DEMO-0005', timeout=3) as response:
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])
            notice = json.load(response)
            self.assertIsNone(notice['deadline'])
            self.assertEqual(len(notice['deadline_evidence']), 2)

    def test_only_allowlisted_paths_are_served(self):
        for path in ('/seed.py', '/data/sample_notices.json', '/static/../server.py', '/api/notices/missing'):
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                urlopen(self.base_url + path, timeout=3)
            self.assertEqual(error.exception.code, 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
