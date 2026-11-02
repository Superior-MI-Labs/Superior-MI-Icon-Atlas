"""Contract tests for authored logical canvas and crop geometry in real pack ZIPs."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image
from tools.validate_visual_pack import check


def fixture(path: Path, edits=None):
    png = io.BytesIO()
    Image.new('RGBA', (64, 64), (255, 140, 20, 255)).save(png, format='PNG')
    region = {
        'id': 'test.anim.frame01', 'kind': 'region', 'texture': 'sheet',
        'rect_px': [0, 0, 32, 36],
        'logical_size_px': [48, 64],
        'trim_offset_px': [8, 16],
        'pivot': [0.5, 1]
    }
    if edits:
        edits(region)
    pack = {'schema': 'smi-visual-pack/1', 'pack_id': 'test.anim.trim',
            'version': '0.1.0',
            'textures': {'sheet': {'path': 'textures/sheet.png', 'width_px': 64, 'height_px': 64}},
            'assets': [region]}
    with ZipFile(path, 'w', ZIP_DEFLATED) as z:
        z.writestr('manifest.json', json.dumps(pack))
        z.writestr('textures/sheet.png', png.getvalue())


class TrimmedFrameValidationTests(unittest.TestCase):
    def verify(self, edits=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'trim.zip'
            fixture(path, edits)
            return check(path)

    def test_valid_logical_trim_and_foot_anchor(self):
        self.assertEqual(self.verify(), [])

    def test_trim_without_logical_canvas_rejected(self):
        issues = self.verify(lambda r: r.pop('logical_size_px'))
        self.assertTrue(any('requires logical canvas' in e for e in issues), issues)

    def test_trim_overflows_logical_canvas_rejected(self):
        issues = self.verify(lambda r: r.update(trim_offset_px=[20, 30]))
        self.assertTrue(any('outside logical canvas' in e for e in issues), issues)

    def test_negative_trim_offset_rejected(self):
        issues = self.verify(lambda r: r.update(trim_offset_px=[-2, 1]))
        self.assertTrue(any('outside logical canvas' in e for e in issues), issues)

    def test_nine_slice_and_trim_are_incompatible(self):
        issues = self.verify(lambda r: r.update(nine_slice_px=[2, 2, 2, 2]))
        self.assertTrue(any('cannot be combined' in e for e in issues), issues)

    def test_legacy_logical_size_without_trim_remains_valid(self):
        self.assertEqual(self.verify(lambda r: r.pop('trim_offset_px')), [])


if __name__ == '__main__':
    unittest.main()
