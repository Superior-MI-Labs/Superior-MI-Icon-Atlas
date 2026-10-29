"""Stop regressions where the event value changes but the visible HUD does not."""
import json
import unittest
from pathlib import Path
from zipfile import ZipFile
from tools.build_site import ROOT,build
from tools.validate_visual_pack import check
from tools.ai_acceptance import check_acceptance

class HUDChecks(unittest.TestCase):
    def test_source_layers_and_bounds(self):
        manifest=json.loads((ROOT/'examples/interactive-hud/manifest.json').read_text())
        meter=next(a for a in manifest['assets'] if a['id']=='smi.example.hud.meter')
        self.assertEqual((meter['inputs']['value']['min'],meter['inputs']['value']['max']),(0,100))
        self.assertEqual([l['id'] for l in meter['layers']],['frame','fill','thumb'])
        self.assertEqual(next(l for l in meter['layers'] if l['id']=='fill')['clip']['input'],'value')
        self.assertEqual(next(l for l in meter['layers'] if l['id']=='thumb')['position_from_input']['input'],'value')
    def test_reject_invalid_numeric_range(self):
        from tempfile import TemporaryDirectory
        from zipfile import ZipFile,ZIP_DEFLATED
        with TemporaryDirectory() as d:
            original=ROOT/'examples/interactive-hud'
            data=json.loads((original/'manifest.json').read_text())
            meter=next(a for a in data['assets'] if a['id']=='smi.example.hud.meter')
            meter['inputs']['value']['max']=0
            archive=Path(d)/'bad.zip'
            with ZipFile(archive,'w',ZIP_DEFLATED) as z:
                z.writestr('manifest.json',json.dumps(data))
                z.write(original/'textures/atlas.png','textures/atlas.png')
            problems=check(archive)
            self.assertTrue(any('invalid min/max' in x for x in problems),problems)

    def test_generated_pack_and_request_specific_gate(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as d:
            dst=Path(d);build(dst)
            archive=dst/'demo/interactive-hud.zip'
            self.assertEqual(check(archive),[])
            spec=json.loads((ROOT/'examples/acceptance/interactive-hud.json').read_text())
            self.assertEqual(check_acceptance(archive,spec),[])
            spec['checks'].append({'type':'layer_order','asset':'smi.example.hud.meter','before':'fill','after':'frame'})
            self.assertTrue(check_acceptance(archive,spec))

if __name__=='__main__':unittest.main()
