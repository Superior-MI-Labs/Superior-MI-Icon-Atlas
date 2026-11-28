import copy
import json
import tempfile
from pathlib import Path
import unittest
from zipfile import ZipFile
from PIL import Image
from tools.validate_visual_pack import check

CONCEPT={'schema':'smi-concept/1','id':'test.sword','name':'Sword','license':'CC0-1.0',
         'capabilities':['repairable'],'relationships':[{'kind':'requires','target':{'kind':'concept','id':'test.iron'}}],
         'state_axes':{'condition':{'kind':'ratio','current':'durability.current','maximum':'durability.max',
                                    'bands':[{'max':0,'state':'broken'},{'max':1,'state':'intact'}]}}}
ASSET={'id':'test.sword.icon','concept_id':'test.sword','kind':'region','texture':'t','rect_px':[0,0,1,1],
       'representation':{'role':'inventory','when':{'condition':'broken'}}}

class ConceptGraphTests(unittest.TestCase):
    def validate(self, concept, asset):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            Image.new('RGBA',(1,1),(255,0,0,255)).save(path/'sheet.png')
            pack={'schema':'smi-visual-pack/1','pack_id':'test.graph','version':'1','license':'CC0-1.0',
                  'textures':{'t':{'path':'sheet.png','width_px':1,'height_px':1}},'assets':[asset],
                  'concepts':[concept] if concept is not None else []}
            with ZipFile(path/'test.zip','w') as z:
                z.writestr('manifest.json',json.dumps(pack))
                z.write(path/'sheet.png','sheet.png')
            return check(path/'test.zip')

    def test_semantic_unresolved_reference_and_valid_selector(self):
        self.assertEqual(self.validate(CONCEPT,ASSET),[])

    def test_bad_ratio_bands(self):
        c=copy.deepcopy(CONCEPT)
        c['state_axes']['condition']['bands'][-1]['max']=.9
        self.assertTrue(any('Invalid ratio state bands' in e for e in self.validate(c,ASSET)))

    def test_missing_concept_or_unknown_selector(self):
        self.assertTrue(any('Missing representation concept' in e for e in self.validate(None,ASSET)))
        a=copy.deepcopy(ASSET)
        a['representation']['when']['condition']='unknown'
        self.assertTrue(any('Invalid representation selector' in e for e in self.validate(CONCEPT,a)))

    def test_unknown_relation(self):
        c=copy.deepcopy(CONCEPT)
        c['relationships'][0]['kind']='execute'
        self.assertTrue(self.validate(c,ASSET))
