"""Shared authoring conformance: schema plus cross-field semantics."""
import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from tools.validate_visual_pack import discovery_offer_errors
ROOT=Path(__file__).resolve().parents[1]
class DiscoveryOfferTests(unittest.TestCase):
    def test_shared_contract(self):
        schema=json.loads((ROOT/'schemas/smi-visual-pack-v1.schema.json').read_text())
        schema['$ref']='#/$defs/concept'
        # The root pack schema also contains constraints. Validate the concept
        # fragment with the same definitions, not an unrelated pack object.
        validator=Draft202012Validator({'$defs':schema['$defs'],'$ref':'#/$defs/concept'})
        for item in json.loads((ROOT/'tests/fixtures/offer-validation-fixtures.json').read_text()):
            with self.subTest(case=item['name']):
                c={'schema':'smi-concept/1','id':'test.offer','name':'Test offer','license':'CC0-1.0','discovery_offers':item['offers']}
                valid=validator.is_valid(c)
                if valid: valid=not discovery_offer_errors(c)
                self.assertEqual(valid,item['valid'])
    def test_legacy_concept_stays_valid(self):
        schema=json.loads((ROOT/'schemas/smi-visual-pack-v1.schema.json').read_text())
        v=Draft202012Validator({'$defs':schema['$defs'],'$ref':'#/$defs/concept'})
        self.assertTrue(v.is_valid({'schema':'smi-concept/1','id':'test.old','name':'Old','license':'CC0-1.0'}))
        self.assertEqual(discovery_offer_errors({'id':'test.old'}),[])
