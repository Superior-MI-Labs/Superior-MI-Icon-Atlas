"""Cross-runtime schema and semantic gates for optional preview control profiles."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image
from tools.validate_visual_pack import check

class PreviewProfileTests(unittest.TestCase):
    def verify(self, profile, asset=None):
        state_set=asset or {"id":"demo.states","kind":"state_set","states":{"idle":"demo.idle","walk":"demo.walk"},"default_state":"idle"}
        pack={"schema":"smi-visual-pack/1","pack_id":"demo.profile","version":"1.0.0","license":"CC0-1.0",
              "textures":{"atlas":{"path":"textures/a.png","width_px":2,"height_px":2}},
              "assets":[
                  {"id":"demo.idle","kind":"region","texture":"atlas","rect_px":[0,0,1,1]},
                  {"id":"demo.walk","kind":"region","texture":"atlas","rect_px":[1,0,1,1]},
                  state_set],"preview_profiles":[profile]}
        pixels=io.BytesIO();Image.new("RGBA",(2,2),(0,0,0,0)).save(pixels,format="PNG")
        with tempfile.TemporaryDirectory() as d:
            archive=Path(d)/"pack.zip"
            with ZipFile(archive,"w",ZIP_DEFLATED) as z:
                z.writestr("manifest.json",json.dumps(pack))
                z.writestr("textures/a.png",pixels.getvalue())
            return check(archive)

    def test_platformer_and_custom_mapping_validate(self):
        p={"schema":"smi-preview-controls/1","id":"demo.platformer","asset":"demo.states",
           "neutral":{"state":"idle"},
           "actions":{"move":{"mode":"hold","target":{"state":"walk"}}},
           "bindings":[{"device":"keyboard","code":"ArrowRight","action":"move"},
                       {"device":"gamepad_button","button":15,"action":"move"}]}
        self.assertEqual(self.verify(p),[])
        self.assertTrue(self.verify({**p,"neutral":{"state":"missing"}}))
        self.assertTrue(self.verify({**p,"actions":{"move":{"mode":"hold","target":{"state":"missing"}}}}))
        self.assertTrue(self.verify({**p,"bindings":p["bindings"]+[p["bindings"][0]]}))
        self.assertTrue(self.verify({**p,"bindings":[{"device":"keyboard","code":"ArrowRight","action":"unknown"}]}))
        self.assertTrue(self.verify({**p,"actions":{"move":{"mode":"hold","target":{"event":"walk"}}}}))

if __name__=="__main__":unittest.main()
