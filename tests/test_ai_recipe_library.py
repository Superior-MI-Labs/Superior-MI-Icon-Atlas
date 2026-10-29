"""Regression gates: working AI recipe files and generated Explore pack discovery."""
import json
import re
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from tools.build_site import build, ROOT
from tools.validate_visual_pack import check
from tools.qualify_asset_zip import scan

EXAMPLES=('icons','animated-icons','character-animations','interactive-hud')

class AIRecipeLibraryTests(unittest.TestCase):
    def test_required_short_handoff_and_categorized_recipes(self):
        docs=ROOT/'docs/ai'
        start=(docs/'START-HERE.md').read_text()
        self.assertLess(len(start),4200,'The AI entrypoint must remain compact')
        self.assertGreaterEqual(start.count('- [ ]'),5)
        for name in ('INDEX.md','FORMAT-API.md','RELEASE-CHECKLIST.md'):
            self.assertTrue((docs/name).is_file(),name)
        for folder in ('icons','animations','gui','collections','materials'):
            path=docs/folder/'README.md'
            self.assertTrue(path.is_file(),str(path))
            self.assertIn('RELEASE-CHECKLIST.md',path.read_text())
        checklist=(docs/'RELEASE-CHECKLIST.md').read_text()
        for field in ('creator-specific','every asset region','NOT RUN','READY FOR PREVIEW','minimum, midpoint, maximum','layer order'):
            self.assertIn(field.lower(),checklist.lower())

    def test_example_zip_structure_and_visual_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            site=Path(tmp)/'site';build(site)
            for example in EXAMPLES:
                path=site/'demo'/f'{example}.zip'
                self.assertTrue(path.is_file(),example)
                self.assertEqual(check(path),[],example)
                report=scan(path,Path(tmp)/example)
                self.assertEqual(report['validation'],'PASS',str(report['errors']))
                self.assertTrue(report['regions'])
                self.assertTrue(report['contact_sheets'])
                self.assertTrue(any(x['kind'] in {'sequence','composition','state_set'} for x in json.loads(ZipFile(path).read('manifest.json'))['assets']) or example=='icons')

    def test_required_request_specific_acceptance_passes_and_rejects_wrong_preset(self):
        from tools.ai_acceptance import check_acceptance
        with tempfile.TemporaryDirectory() as tmp:
            site=Path(tmp);build(site)
            spec=json.loads((ROOT/'examples/acceptance/character.json').read_text())
            self.assertEqual(check_acceptance(site/'demo/character-animations.zip',spec),[])
            spec['checks'].append({'type':'state_contains','asset':'smi.example.robot.states','state':'fly'})
            self.assertTrue(check_acceptance(site/'demo/character-animations.zip',spec))
            potion=json.loads((ROOT/'examples/acceptance/potion.json').read_text())
            self.assertEqual(check_acceptance(site/'demo/potions-collection.zip',potion),[])
            potion['checks'][1]['option']='smi.fluid.not-present'
            self.assertTrue(check_acceptance(site/'demo/potions-collection.zip',potion))

    def test_generated_featured_index_and_template_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            site=Path(tmp);build(site)
            d=json.loads((site/'featured-packs.json').read_text())
            self.assertEqual(d['schema'],'smi-featured-packs/1')
            names={pack['filename'] for pack in d['packs']}
            self.assertTrue({f'{e}.zip' for e in EXAMPLES}.issubset(names))
            self.assertTrue({'starter-pack.zip','potions-collection.zip'}.issubset(names))
            for item in d['packs']:
                self.assertTrue((site/'demo'/item['filename']).is_file())
                self.assertGreater(item['assets'],0)
                self.assertGreater(item['manifests'],0)
                self.assertTrue(item['entry'])
                self.assertTrue(item['kinds'])
            self.assertIn('featured.js',(site/'index.html').read_text())
            self.assertIn('featured-packs.json',(site/'featured.js').read_text())
            self.assertIn("get('example')",(site/'builder.js').read_text())

    def test_local_ai_links_resolve_in_generated_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            site=Path(tmp);build(site)
            markdown=list((site/'ai').rglob('*.md'))
            self.assertGreaterEqual(len(markdown),10)
            failures=[]
            for doc in markdown:
                for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
                    if link.startswith(('https://','http://','#','mailto:')):continue
                    path=link.split('#',1)[0]
                    if not (doc.parent/path).resolve().is_file():failures.append((str(doc.relative_to(site)),path))
            self.assertEqual(failures,[])

if __name__=='__main__':unittest.main()
