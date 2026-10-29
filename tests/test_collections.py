"""Collection ZIP interoperability, cross-manifest references, event-output contracts."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from PIL import Image
from tools.validate_visual_pack import check

class CollectionContractTests(unittest.TestCase):
    @staticmethod
    def make_zip(path, manifest_count=20, invalid=None):
        image=Image.new('RGBA',(32,32),(12,180,220,220))
        buffer=io.BytesIO();image.save(buffer,format='PNG');data=buffer.getvalue()
        index={'schema':'smi-visual-collection/1','collection_id':'example.character-pack','name':'20-sheet Character Collection','version':'1.0.0','entry_asset':'example.character.complete','packs':[]}
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for i in range(manifest_count):
                folder=f'packs/sheet-{i:02d}'
                index['packs'].append({'manifest':folder+'/manifest.json','label':f'Sheet {i}'})
                asset={'id':f'example.sheet{i}.frame','kind':'region','texture':'main','rect_px':[0,0,32,32]}
                assets=[asset]
                if i == manifest_count-1:
                    asset={'id':'example.character.complete','kind':'composition','name':'Complete Character','size_px':[32,32],
                        'inputs':{'animation':{'type':'enum','default':'idle','values':['idle','attack','hurt']}},
                        'behavior':{'role':'actor','outputs':{'state':{'from_input':'animation'}},'on':{'hit':[{'op':'set','input':'animation','value':'hurt'},{'op':'emit','event':'state_changed'}]}},
                        'layers':[{'id':'body','asset':'example.sheet0.frame'}, {'id':'equipment','asset':f'example.sheet{i}.frame'}]}
                    if invalid=='reference':asset['layers'][0]['asset']='example.missing'
                    if invalid=='behavior':asset['behavior']['outputs']['state']['from_input']='missing_input'
                    assets.append(asset)
                pack={'schema':'smi-visual-pack/1','pack_id':f'example.sheet{i}','version':'1.0.0','license':'CC0-1.0','textures':{'main':{'path':'textures/sheet.png','width_px':32,'height_px':32}},'assets':assets}
                z.writestr(folder+'/manifest.json',json.dumps(pack));z.writestr(folder+'/textures/sheet.png',data)
            if invalid=='index':index['packs'].pop()
            z.writestr('collection.json',json.dumps(index))

    def test_valid_collection_with_twenty_manifests_and_events(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'valid.zip';self.make_zip(path)
            self.assertEqual(check(path),[])
    def test_broken_cross_manifest_reference_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'broken.zip';self.make_zip(path,invalid='reference')
            self.assertTrue(any('Unknown referenced asset' in e for e in check(path)))
    def test_undefined_behavior_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'broken.zip';self.make_zip(path,invalid='behavior')
            self.assertTrue(any('unknown output source' in e for e in check(path)))
    def test_index_omission_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'broken.zip';self.make_zip(path,invalid='index')
            self.assertTrue(any('enumerate every' in e for e in check(path)))

if __name__=='__main__':unittest.main()
