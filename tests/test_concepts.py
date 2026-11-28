"""Exercise the official ZIP validator on the shared concept fixture."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from PIL import Image
from tools.validate_visual_pack import check

POTION = json.loads((Path(__file__).parent / 'fixtures/concept-potion.json').read_text())


class ConceptContractTests(unittest.TestCase):
    def validate(self, definitions, linked=True, duplicate=False):
        def pack(name, concepts=None, link=True):
            a = {'id': name + '.icon', 'kind': 'region', 'texture': 't', 'rect_px': [0, 0, 1, 1]}
            if link:
                a['concept_id'] = POTION['id']
            p = {'schema': 'smi-visual-pack/1', 'pack_id': name, 'version': '1',
                 'textures': {'t': {'path': 'image.png', 'width_px': 1, 'height_px': 1}}, 'assets': [a]}
            if concepts is not None:
                p['concepts'] = concepts
            return p
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'test.zip'
            pixels = io.BytesIO()
            Image.new('RGBA', (1, 1), 'red').save(pixels, format='PNG')
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('a/manifest.json', json.dumps(pack('a', definitions, linked)))
                z.writestr('a/image.png', pixels.getvalue())
                if duplicate:
                    z.writestr('b/manifest.json', json.dumps(pack('b', definitions)))
                    z.writestr('b/image.png', pixels.getvalue())
            return check(path)

    def test_legacy_and_valid(self):
        self.assertEqual(self.validate(None), [])
        self.assertEqual(self.validate([POTION]), [])

    def test_duplicate_or_orphan(self):
        self.assertTrue(any('Duplicate concept' in e for e in self.validate([POTION], duplicate=True)))
        self.assertTrue(any('Unreferenced concept' in e for e in self.validate([POTION], linked=False)))

    def test_bad_dimensions_defaults_and_code(self):
        for key, value in [('height_m', -1), ('width_ft', 2), ('mass_kg', 0)]:
            p = copy.deepcopy(POTION)
            p['physical'][key] = value
            self.assertTrue(self.validate([p]))
        for key, value in [('count', 0), ('sides', 1), ('modifier', 0.5)]:
            p = copy.deepcopy(POTION)
            p['defaults']['smi.rules.d20/1']['health.restore'][key] = value
            self.assertTrue(self.validate([p]))
        p = copy.deepcopy(POTION)
        p['script'] = 'arbitrary code'
        self.assertTrue(self.validate([p]))
        p = copy.deepcopy(POTION)
        p['defaults']['unversioned'] = p['defaults'].pop('smi.rules.d20/1')
        self.assertTrue(self.validate([p]))


if __name__ == '__main__':
    unittest.main()
