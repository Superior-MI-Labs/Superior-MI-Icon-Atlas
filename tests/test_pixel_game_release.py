"""Published icon pack contracts, using the existing validator and creator-specific acceptance."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'examples/pixel-fantasy-icons'

class PixelGameReleaseTests(unittest.TestCase):
    def test_48_items_and_alpha_baselines(self):
        result=subprocess.run([sys.executable,str(SOURCE/'verify_pack.py')],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_existing_pack_validator_and_creator_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive=Path(tmp)/'pixel-fantasy-icons.zip'
            import importlib.util
            sys.path.insert(0,str(SOURCE))
            try:
                spec=importlib.util.spec_from_file_location('pixel_pack',SOURCE/'package_candidate.py')
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                module.build(archive)
            finally:
                sys.path.remove(str(SOURCE))
            for args in (['tools/validate_visual_pack.py',str(archive)],
                         ['tools/ai_acceptance.py',str(archive),'--acceptance',str(SOURCE/'qa/acceptance.json'),'--out',str(Path(tmp)/'acceptance')]):
                result=subprocess.run([sys.executable,*args],capture_output=True,text=True,cwd=ROOT)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_published_once(self):
        publications=json.loads((ROOT/'publications.json').read_text())['collections']
        published=[c for c in publications if c['path']=='examples/pixel-fantasy-icons']
        self.assertEqual(len(published),1)
        self.assertEqual(published[0]['expected_assets'],65)
        manifest=json.loads((SOURCE/'manifest.json').read_text())
        self.assertEqual(len(manifest['assets']),65)
        self.assertEqual(len([a for a in manifest['assets'] if a['kind']=='region' and a['texture']!='effects']),48)
        self.assertEqual(len([a for a in manifest['assets'] if a['kind']=='region' and a['texture']=='effects']),14)
        self.assertTrue(all(a.get('style') for a in manifest['assets']))

    def test_real_builder_recipe_covers_every_item(self):
        import importlib.util
        module_spec=importlib.util.spec_from_file_location('pixel_browser_matrix',ROOT/'tests/browser_visual_matrix.py')
        browser_visual_matrix=importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(browser_visual_matrix)
        spec=json.loads((ROOT/'tests/pixel-release-scenarios.json').read_text())
        browser_visual_matrix.verify_spec(spec)
        covered=[s['slots']['icon'] for case in spec['cases'] for s in case['samples'] if 'slots' in s]
        manifest=json.loads((SOURCE/'manifest.json').read_text())
        items={a['id'] for a in manifest['assets'] if a['kind']=='region' and a['texture']!='effects'}
        self.assertEqual(set(covered),items)

if __name__=='__main__':unittest.main()
