"""Public catalog is built only from explicitly approved source collections."""
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from tools.build_site import build,ROOT
from tools.prune_public_site import prune
from tools.validate_visual_pack import check

class PublicCatalogTests(unittest.TestCase):
    def test_public_approval_and_manifest_derived_records(self):
        with tempfile.TemporaryDirectory() as temp:
            site=Path(temp);build(site)
            public=json.loads((site/'public-catalog.json').read_text())
            self.assertEqual(public['schema'],'smi-public-catalog/1')
            self.assertEqual(len(public['packs']),1)
            self.assertEqual(public['packs'][0]['id'],'fantasy-rpg-hud-wave1')
            pack=json.loads((ROOT/'examples/fantasy-rpg-hud-wave1/manifest.json').read_text())
            self.assertEqual({a['id'] for a in pack['assets']},{a['id'] for a in public['assets']})
            self.assertEqual(len(public['assets']),70)
            self.assertEqual(check(site/'demo/fantasy-rpg-hud-wave1.zip'),[])
            self.assertTrue(all(a['license']=='CC0-1.0' for a in public['assets']))
            home=(site/'index.html').read_text().lower()
            self.assertNotIn('browse the 2,073-icon library',home)
            self.assertNotIn('white geometric monoline',home)
            self.assertNotIn('explore asset packs and starter templates',home)
            self.assertNotIn('featured.js',home)
            self.assertIn('asset-renderer.js',home)
            self.assertNotIn('catalog-data.js',home)
            self.assertIn('public-catalog.json',(site/'app.js').read_text())
            self.assertIn('asset-renderer.js',(site/'builder.html').read_text())
    def test_deployed_site_excludes_old_public_files_and_starter_zips(self):
        with tempfile.TemporaryDirectory() as temp:
            site=Path(temp);build(site)
            self.assertEqual(prune(site),1)
            self.assertTrue((site/'demo/fantasy-rpg-hud-wave1.zip').is_file())
            for rel in ('catalog-data.js','featured-packs.json','manifest.json','sheets','manifests','demo/starter-pack.zip','demo/animated-icons.zip','demo/interactive-hud.zip'):
                self.assertFalse((site/rel).exists(),rel)

    def test_legacy_sources_remain_archived(self):
        self.assertTrue((ROOT/'manifest.json').is_file())
        self.assertTrue((ROOT/'examples/icons/manifest.json').is_file())
        public=json.loads((ROOT/'publications.json').read_text())
        self.assertEqual(public['collections'][0]['path'],'examples/fantasy-rpg-hud-wave1')

if __name__=='__main__':unittest.main()