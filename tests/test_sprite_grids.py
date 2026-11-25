"""Pixel-level checks for the published reference PNGs."""
import io
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
from PIL import Image
from tools.sprite_grids import LAYOUTS, build_sprite_grids


class SpriteGridTests(unittest.TestCase):
    def test_reference_pngs_and_archive(self):
        self.assertEqual(len(LAYOUTS), 11)
        self.assertEqual(len(set(LAYOUTS)), len(LAYOUTS))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_sprite_grids(root)
            archive_path = root / "sprite-grid-references.zip"
            before = archive_path.read_bytes()
            with ZipFile(archive_path) as archive:
                self.assertIsNone(archive.testzip())
                expected = {f"grid-{c}x{r}-{p}px.png" for c, r, p in LAYOUTS}
                self.assertEqual(set(archive.namelist()), expected)
                page = (root / "sprite-grids" / "index.html").read_text()
                for c, r, p in LAYOUTS:
                    name = f"grid-{c}x{r}-{p}px.png"
                    self.assertIn(f'href="{name}"', page)
                    data = archive.read(name)
                    self.assertEqual(data, (root / "sprite-grids" / name).read_bytes())
                    with Image.open(io.BytesIO(data)) as im:
                        w, h = c * p, r * p
                        self.assertEqual(im.mode, "RGBA")
                        self.assertEqual(im.size, (w, h))
                        # Independent expected mask: two-pixel outer borders and
                        # a one-pixel band on either side of each internal division.
                        from PIL import ImageDraw, ImageChops
                        expected_image = Image.new("RGBA", (w, h))
                        draw = ImageDraw.Draw(expected_image)
                        gray = (128, 128, 128, 255)
                        for x in [0, w-2] + [i*p-1 for i in range(1, c)]:
                            draw.rectangle((x, 0, x+1, h-1), fill=gray)
                        for y in [0, h-2] + [i*p-1 for i in range(1, r)]:
                            draw.rectangle((0, y, w-1, y+1), fill=gray)
                        difference = ImageChops.difference(im, expected_image)
                        self.assertTrue(all(band.getbbox() is None for band in difference.split()), name)
            build_sprite_grids(root)
            self.assertEqual(archive_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
