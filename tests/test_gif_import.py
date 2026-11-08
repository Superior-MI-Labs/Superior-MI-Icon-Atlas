"""GIF QA must reject opaque sequences and preserve frame duration/alpha."""
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageDraw
from tools.import_gif import decode, inspect, package, main

class GifImportTests(unittest.TestCase):
    def create_gif(self, path, opaque=False):
        frames=[]
        for i in range(4):
            image=Image.new("RGBA",(72,96),(1,1,1,255) if opaque else (0,0,0,0))
            draw=ImageDraw.Draw(image)
            draw.ellipse((24+4*i,30,52+4*i,60),fill=(250,106,12,255))
            frames.append(image)
        frames[0].save(path,save_all=True,append_images=frames[1:],duration=[80,90,120,70],loop=0,disposal=2,transparency=0,optimize=False)
    def test_review_gate_and_runtime_pack(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);gif=root/"good.gif";self.create_gif(gif)
            frames,delays,warnings=decode(gif)
            self.assertEqual(delays,[80,90,120,70])
            report=inspect(frames,delays,warnings)
            self.assertEqual(report["errors"],[])
            self.assertEqual(main([str(gif),"--out",str(root/"review")]),0)
            with self.assertRaisesRegex(ValueError,"approve-visual"):
                main([str(gif),"--out",str(root/"review"),"--pack",str(root/"ready.zip"),"--id","test.idle"])
            self.assertEqual(main([str(gif),"--out",str(root/"review"),"--pack",str(root/"ready.zip"),
                "--id","test.idle","--approve-visual","--license","CC0-1.0"]),0)
            with ZipFile(root/"ready.zip") as zipfile:
                manifest=json.loads(zipfile.read("manifest.json"))
                self.assertEqual(len(manifest["assets"]),5)
                self.assertEqual(manifest["assets"][-1]["playback"],"loop")
                self.assertEqual([f["duration_ms"] for f in manifest["assets"][-1]["frames"]],delays)
                self.assertTrue(zipfile.testzip() is None)
                self.assertIn("qa-report.json",zipfile.namelist())
    def test_opaque_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);gif=root/"opaque.gif";self.create_gif(gif,opaque=True)
            frames,delays,warnings=decode(gif)
            self.assertTrue(inspect(frames,delays,warnings)["errors"])
            with self.assertRaisesRegex(ValueError,"Structural QA failed"):
                main([str(gif),"--out",str(root/"review"),"--pack",str(root/"not-ready.zip"),
                    "--id","test.run","--approve-visual"])

if __name__=="__main__":
    unittest.main()
