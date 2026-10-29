import unittest
import tempfile
import hashlib
from pathlib import Path
from PIL import Image
from tools.build_site import build, ROOT
from atlasctl import validate, load

class AtlasContractTests(unittest.TestCase):
    def test_atlas_geometry_manifest(self):
        self.assertEqual(validate(), [])
        m=load();self.assertEqual(len(m['icons']),2073)
        self.assertEqual(len(m['sheets']),20)
        self.assertEqual(len({i['id'] for i in m['icons']}),len(m['icons']))
        self.assertTrue(all(i['provenance']['source_path'].startswith('source-images/') for i in m['icons']))

    def test_real_alpha_and_cell_boundaries(self):
        m=load()
        bysheet={s['path']:[] for s in m['sheets']}
        for i in m['icons']:bysheet[i['sheet']].append(i)
        for sheet in m['sheets']:
            image=Image.open(ROOT/sheet['path']).convert('RGBA')
            self.assertEqual(image.size,(2304,768))
            self.assertEqual(hashlib.sha256((ROOT/sheet['path']).read_bytes()).hexdigest(),sheet['sha256'])
            assert (ROOT/sheet['foreground_mask']).is_file()
            assert (ROOT/sheet['black_outline']).is_file()
            for icon in bysheet[sheet['path']]:
                rect=icon['rect_px'];bbox=(rect['x'],rect['y'],rect['x']+96,rect['y']+96)
                crop=image.crop(bbox)
                alpha=crop.getchannel('A')
                self.assertIsNotNone(alpha.getbbox(),icon['id'])
                self.assertFalse(alpha.crop((0,0,96,5)).getbbox(),icon['id'])
                self.assertFalse(alpha.crop((0,91,96,96)).getbbox(),icon['id'])
                self.assertFalse(alpha.crop((0,0,5,96)).getbbox(),icon['id'])
                self.assertFalse(alpha.crop((91,0,96,96)).getbbox(),icon['id'])
                self.assertEqual(hashlib.sha256(crop.tobytes()).hexdigest(),icon['crop_rgba_sha256'])
                pix=crop.getpixel((48,48))
                # Test all occupied pixels are tintable white, never baked black.
                if alpha.getbbox():
                    self.assertEqual(crop.getchannel('R').getextrema()[1],255)
            occupied={(i['cell']['x'],i['cell']['y']) for i in bysheet[sheet['path']]}
            for row in range(8):
                for col in range(24):
                    if (col,row) not in occupied:
                        self.assertFalse(image.crop((col*96,row*96,(col+1)*96,(row+1)*96)).getchannel('A').getbbox())

    def test_website_build(self):
        with tempfile.TemporaryDirectory() as temp:
            site=Path(temp)
            self.assertEqual(build(site),2073)
            self.assertTrue((site/'index.html').is_file())
            self.assertTrue((site/'catalog-data.js').is_file())
            self.assertTrue((site/'sheets/developer-tools-00/atlas.png').is_file())
            text=(site/'catalog-data.js').read_text()
            self.assertIn('icons.candidate.developer-tools',text)

if __name__=='__main__':unittest.main()
