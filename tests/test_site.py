"""Zero-dependency contract tests for the static/offline Icon Atlas browser."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_site import build


class TestSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))

    def test_all_manifest_ids_unique_and_safe_for_downloads(self):
        icons = self.manifest['icons']
        self.assertEqual(len(icons), len({a['id'] for a in icons}))
        for a in icons:
            self.assertRegex(a['id'], r'^icons\.[a-z0-9_.-]+$')
            self.assertEqual(a['rect_px']['w'], 96)
            self.assertEqual(a['rect_px']['h'], 96)
            self.assertIn('source', a)

    def test_build_from_manifest_without_external_dependencies(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / 'site'
            self.assertEqual(build(dest), len(self.manifest['icons']))
            for name in ('index.html','app.js','styles.css','manifest.json','catalog-data.js','LICENSE','NOTICE.md','.nojekyll'):
                self.assertTrue((dest / name).is_file(), name)
            data = (dest / 'catalog-data.js').read_text(encoding='utf-8')
            self.assertTrue(data.startswith('"use strict";window.ICON_ATLAS_DATA='))
            js = data.split('window.ICON_ATLAS_DATA=',1)[1].rsplit(';',1)[0]
            parsed = json.loads(js)
            self.assertEqual(set(x['id'] for x in parsed['icons']), set(x['id'] for x in self.manifest['icons']))
            self.assertEqual(parsed['icons'][0]['rect_px'], self.manifest['icons'][0]['rect_px'])
            sh = self.manifest['sheet']
            for field in ('path','foreground_mask','black_outline'):
                self.assertEqual((dest / sh[field]).read_bytes(), (ROOT / sh[field]).read_bytes())

    def test_sheet_is_true_rgba_png_and_hashed(self):
        sh = self.manifest['sheet']
        path = ROOT / sh['path']
        content = path.read_bytes()
        self.assertEqual(content[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>II', content[16:24]), (sh['width_px'], sh['height_px']))
        self.assertEqual(content[25], 6, 'PNG must have RGBA channel')
        self.assertEqual(hashlib.sha256(content).hexdigest(), sh['sha256'])
        for a in self.manifest['icons']:
            r = a['rect_px']
            self.assertEqual(r['x'], a['cell']['x'] * sh['cell_px'])
            self.assertEqual(r['y'], a['cell']['y'] * sh['cell_px'])

    def test_download_uses_manifest_id_not_display_name(self):
        code = (ROOT / 'web/app.js').read_text(encoding='utf-8')
        self.assertIn("a.download=item.id+'.png'", code)
        self.assertIn('ctx.drawImage(sprite,r.x,r.y,r.w,r.h,0,0,r.w,r.h)',code)
        self.assertIn('drawImage(outline',code)
        self.assertIn('source-in',code)
        self.assertIn('URL.createObjectURL(blob)',code)

    def test_pages_workflow_uses_only_generated_site(self):
        workflow = (ROOT / '.github/workflows/pages.yml').read_text(encoding='utf-8')
        self.assertIn('python3 tools/build_site.py',workflow)
        self.assertIn('actions/upload-pages-artifact@v4',workflow)
        self.assertIn('actions/deploy-pages@v4',workflow)
        self.assertIn('path: site/',workflow)


if __name__ == '__main__':
    unittest.main()
