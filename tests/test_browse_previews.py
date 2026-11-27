import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from tools.browse_previews import build_region_previews

class BrowsePreviewTests(unittest.TestCase):
    def test_exact_crop_dedup_and_complex_fallback(self):
        buf=BytesIO()
        with Image.new('RGBA',(400,200),(0,0,0,0)) as im:
            im.paste((255,0,0,255),(20,20,180,180));im.paste((0,255,0,255),(200,0,400,200));im.save(buf,format='PNG')
        region={'id':'a','kind':'region','texture':'t','rect_px':[0,0,200,200]}
        pack={'textures':{'t':{'path':'textures/a.png'}},'assets':[region,{**region,'id':'b'},{**region,'id':'complex','nine_slice_px':[1,1,1,1]},{**region,'id':'hidden','discovery':'hidden'},{**region,'id':'unowned'}]}
        index={'packs':[{'manifest':'sub/manifest.json'}]}
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp);archive=dest/'pack.zip'
            with ZipFile(archive,'w') as z:z.writestr('sub/textures/a.png',buf.getvalue())
            with ZipFile(archive) as z:result=build_region_previews(z,index,[pack],{'a','b','complex','hidden'},dest)
            self.assertEqual(set(result),{'a','b'});self.assertEqual(result['a'],result['b'])
            with Image.open(dest/result['a']) as thumb:
                self.assertEqual(thumb.size,(124,124));self.assertEqual(thumb.getpixel((60,60)),(255,0,0,255));self.assertEqual(thumb.getpixel((0,0))[3],0)
