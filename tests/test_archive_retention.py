import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.retain_archives import archive_path, stage_current, publish_retained


def catalog(data):
    return {'schema': 'smi-public-catalog/1', 'packs': [{
        'id': 'approved', 'zip': 'demo/approved.zip',
        'archive_sha256': hashlib.sha256(data).hexdigest()}]}


def site_version(site, data):
    (site/'demo').mkdir(parents=True, exist_ok=True)
    (site/'demo/approved.zip').write_bytes(data)
    index = catalog(data)
    stage_current(site, index)
    (site/'public-catalog.json').write_text(json.dumps(index))
    return index['packs'][0]['immutable_zip']


class RetentionTests(unittest.TestCase):
    def test_bootstrap_then_two_releases_and_dedup(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            site, store = root/'site', root/'store'
            old = b'prior exact published bytes'
            prior = catalog(old)
            def fetch(path, limit):
                return json.dumps(prior).encode() if path == 'public-catalog.json' else old
            first = site_version(site, b'first qualified release')
            self.assertEqual(publish_retained(site, store, bootstrap=True, fetch=fetch), 2)
            self.assertEqual((site/archive_path(hashlib.sha256(old).hexdigest())).read_bytes(), old)
            self.assertEqual(publish_retained(site, store), 2)
            second = site_version(site, b'second qualified release')
            self.assertNotEqual(first, second)
            self.assertEqual(publish_retained(site, store), 3)
            self.assertEqual((site/first).read_bytes(), b'first qualified release')
            self.assertEqual((site/second).read_bytes(), b'second qualified release')

    def test_missing_history_and_tampering_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            site, store = root/'site', root/'store'
            loc = site_version(site, b'current')
            with self.assertRaisesRegex(ValueError, 'history missing'):
                publish_retained(site, store)
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                publish_retained(site, store, bootstrap=True, fetch=lambda p, n: json.dumps(catalog(b'old')).encode() if p == 'public-catalog.json' else b'bad')
            (site/loc).write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'site bytes mismatch'):
                publish_retained(site, store, bootstrap=True, fetch=lambda p, n: json.dumps(catalog(b'old')).encode() if p == 'public-catalog.json' else b'old')

    def test_lost_branch_does_not_reinitialize(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            site, store = root/'site', root/'store'
            site_version(site, b'current')
            prior = catalog(b'old')
            prior['packs'][0]['immutable_zip'] = archive_path(prior['packs'][0]['archive_sha256'])
            with self.assertRaisesRegex(ValueError, 'recover branch'):
                publish_retained(site, store, bootstrap=True, fetch=lambda p,n: json.dumps(prior).encode())

    def test_budget_never_evicts(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            site, store = root/'site', root/'store'
            site_version(site, b'current')
            prior = catalog(b'old')
            with patch('tools.retain_archives.MAX_SITE', 1):
                with self.assertRaisesRegex(ValueError, 'budget exceeded'):
                    publish_retained(site, store, bootstrap=True, fetch=lambda p,n: json.dumps(prior).encode() if p=='public-catalog.json' else b'old')
            self.assertEqual(len(list(store.glob('*.zip'))), 2)
