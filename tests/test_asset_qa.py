"""Actual pixel QA: signal a missing region and report every real crop."""
import io
import contextlib
import sys
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image
from tools.build_site import ROOT,build
from tools.qualify_asset_zip import scan

class AssetQualityTests(unittest.TestCase):
    def test_potion_pack_regions_and_reports(self):
        with tempfile.TemporaryDirectory() as td:
            results=scan(ROOT/'web/demo/potions-collection.zip',Path(td))
            self.assertEqual(results['validation'],'PASS',results['errors'])
            self.assertGreaterEqual(len(results['regions']),3)
            self.assertTrue(results['contact_sheets'])
            self.assertEqual(len(results['regions']),len({a['id'] for a in results['regions']}))
            self.assertEqual(results['visual_review'],'NOT VERIFIED BY AUTOMATION')
            self.assertTrue((Path(td)/'qa-report.json').is_file())
            self.assertTrue((Path(td)/'qa-receipt.txt').is_file())

    def test_empty_region_fails_even_when_manifest_geometry_is_valid(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'sample.zip'
            png=io.BytesIO();Image.new('RGBA',(96,96),(0,0,0,0)).save(png,format='PNG')
            pack={'schema':'smi-visual-pack/1','pack_id':'smi.tests.empty', 'version':'0.1.0',
                'textures':{'main':{'path':'textures/blank.png','width_px':96,'height_px':96}},
                'assets':[{'kind':'region','id':'smi.tests.blank','texture':'main','rect_px':[0,0,96,96]}]}
            with ZipFile(path,'w',ZIP_DEFLATED) as z:
                z.writestr('manifest.json',json.dumps(pack));z.writestr('textures/blank.png',png.getvalue())
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result=scan(path,Path(td)/'qa')
            self.assertEqual(result['validation'],'FAIL')
            self.assertTrue(any('empty or fully transparent' in e for e in result['errors']))

    def test_full_bleed_pixels_are_warning_by_default_strict_failure(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'sample.zip'
            png=io.BytesIO();Image.new('RGBA',(32,32),(200,40,60,255)).save(png,format='PNG')
            pack={'schema':'smi-visual-pack/1','pack_id':'smi.tests.photo','version':'0.1.0',
                  'textures':{'main':{'path':'textures/filled.png','width_px':32,'height_px':32}},
                  'assets':[{'kind':'region','id':'smi.tests.photo','texture':'main','rect_px':[0,0,32,32]}]}
            with ZipFile(path,'w',ZIP_DEFLATED) as z:
                z.writestr('manifest.json',json.dumps(pack));z.writestr('textures/filled.png',png.getvalue())
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                normal=scan(path,Path(td)/'normal')
            self.assertEqual(normal['validation'],'PASS')
            self.assertTrue(normal['warnings'])
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                strict=scan(path,Path(td)/'strict',True)
            self.assertEqual(strict['validation'],'FAIL')

    def test_website_includes_ai_handoff_and_downloadable_grids(self):
        with tempfile.TemporaryDirectory() as td:
            site=Path(td);build(site)
            for path in ['ai/START-HERE.md','ai/QA-CHECKLIST.md','ai/PROMPT-EXAMPLES.md',
                         'ai/TEMPLATES.md','templates/authoring-grids.zip','ai-guide.html']:
                self.assertTrue((site/path).is_file(),path)
            guide=(site/'ai-guide.html').read_text()
            self.assertLess(len(guide),6500)
            self.assertIn('QA-CHECKLIST.md',guide)

if __name__=='__main__':unittest.main()
