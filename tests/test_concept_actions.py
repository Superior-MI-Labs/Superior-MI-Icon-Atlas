import copy
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/'schemas/smi-visual-pack-v1.schema.json').read_text())
VALIDATOR=Draft202012Validator({'$schema':SCHEMA['$schema'],'$defs':SCHEMA['$defs'],'$ref':'#/$defs/concept'})

class ActionSchemaTests(unittest.TestCase):
    def test_action_contract(self):
        p=json.loads((ROOT/'tests/fixtures/concept-potion.json').read_text())
        p['actions']={'consume':{'kind':'consume','operations':[
            {'op':'inventory.consume','owner':'actor','item':{'id':p['id']},'quantity':1},
            {'op':'stat.change','owner':'actor','stat':'health.current','direction':'increase','magnitude':{'property':'health.restore'}},
            {'op':'inventory.produce','owner':'actor','item':{'id':'test.bottle'},'quantity':1,
             'when':{'property':'consume.return_container','equals':True}}]}}
        self.assertTrue(VALIDATOR.is_valid(p))
        for key,bad in [('op','execute'),('quantity',0),('owner','arbitrary'),('item',{'id':'../bad'})]:
            v=copy.deepcopy(p);v['actions']['consume']['operations'][0][key]=bad
            self.assertFalse(VALIDATOR.is_valid(v),key)
