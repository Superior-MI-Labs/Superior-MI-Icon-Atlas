import copy
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT/'schemas/smi-visual-pack-v1.schema.json').read_text())
VALUE_SCHEMA = {'$schema': SCHEMA['$schema'], '$defs': SCHEMA['$defs'],
                '$ref': '#/$defs/concept_value'}


class ProportionTests(unittest.TestCase):
    def test_typed_value(self):
        validator = Draft202012Validator(VALUE_SCHEMA)
        value = {'kind': 'proportion', 'fraction': 0.08, 'basis': 'target.health.max',
                 'rounding': 'floor', 'unit': 'hp', 'cap': 30}
        self.assertTrue(validator.is_valid(value))
        for key, bad in [('fraction', 11), ('fraction', -1), ('fraction', True),
                         ('basis', ''), ('rounding', 'random'), ('unit', ''), ('cap', -1)]:
            self.assertFalse(validator.is_valid({**value, key: bad}), key)
        for key in ('basis', 'rounding', 'unit', 'fraction'):
            broken = copy.deepcopy(value)
            del broken[key]
            self.assertFalse(validator.is_valid(broken), key)
        self.assertFalse(validator.is_valid({**value, 'script': 'arbitrary code'}))
