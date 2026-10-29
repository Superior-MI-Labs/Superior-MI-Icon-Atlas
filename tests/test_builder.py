"""Static builder deliverables and offline sample pack contract (stdlib + Pillow)."""
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from tools.validate_visual_pack import check
from tools.build_site import build, ROOT

class BuilderContractTests(unittest.TestCase):
    def test_offline_site_contains_builder_and_demo(self):
        with tempfile.TemporaryDirectory() as temp:
            build(Path(temp))
            for rel in ('builder.html','builder.css','builder.js','timeline-core.js','ai-guide.html','vendor/jszip.min.js','vendor/JSZip-LICENSE.md','demo/starter-pack.zip'):
                self.assertTrue((Path(temp)/rel).is_file(),rel)
            html=(Path(temp)/'builder.html').read_text()
            self.assertIn('Import ZIP',html)
            self.assertIn('vendor/jszip.min.js',html)
            self.assertIn('timeline-core.js',html)
            self.assertIn('id="playhead"',html)
            self.assertIn('id="export-frames"',html)
            self.assertNotIn('https://cdn.',html)
    def test_schema_validation_and_dependency_graph(self):
        self.assertEqual(check(ROOT/'web/demo/starter-pack.zip'),[])

    def test_keyframe_demo_roundtrips_schema(self):
        with ZipFile(ROOT/'web/demo/starter-pack.zip') as z:
            data=json.loads(z.read('manifest.json'))
            animated=[a for a in data['assets'] if any(l.get('tracks') for l in a.get('layers',[]))]
            self.assertTrue(animated,'Demo must prove authored keyframes')
            self.assertEqual(animated[0]['duration_ms'],2000)
        self.assertEqual(check(ROOT/'web/demo/starter-pack.zip'),[])

    def test_reject_bad_keyframe_order_and_values(self):
        import io
        from tools.validate_visual_pack import validate_tracks
        bad=[{'property':'opacity','keyframes':[{'time_ms':0,'value':0.5},{'time_ms':100,'value':1.5}]}]
        self.assertTrue(validate_tracks(bad,100,'bad'))
        unordered=[{'property':'x','keyframes':[{'time_ms':150,'value':2},{'time_ms':100,'value':3}]}]
        self.assertTrue(validate_tracks(unordered,200,'unordered'))
        self.assertFalse(validate_tracks([{'property':'x','keyframes':[{'time_ms':0,'value':0},{'time_ms':100,'value':20}]}],200,'valid'))

    def test_demo_pack_contains_real_valid_textures(self):
        z=ROOT/'web/demo/starter-pack.zip'
        with ZipFile(z) as f:
            pack=json.loads(f.read('manifest.json'))
            self.assertEqual(pack['schema'],'smi-visual-pack/1')
            self.assertEqual(pack['license'],'CC0-1.0')
            self.assertTrue({'region','sequence','composition','state_set'}.issubset({a['kind'] for a in pack['assets']}))
            ids={a['id'] for a in pack['assets']}
            self.assertEqual(len(ids),len(pack['assets']))
            for t in pack['textures'].values():
                self.assertIn(t['path'],f.namelist())
                from io import BytesIO
                with Image.open(BytesIO(f.read(t['path']))) as img:
                    self.assertEqual(img.size,(t['width_px'],t['height_px']))
            for a in pack['assets']:
                if a['kind']=='region':
                    t=pack['textures'][a['texture']]
                    x,y,w,h=a['rect_px']
                    self.assertGreater(w,0);self.assertGreater(h,0)
                    self.assertLessEqual(x+w,t['width_px']);self.assertLessEqual(y+h,t['height_px'])
if __name__=='__main__':unittest.main()
