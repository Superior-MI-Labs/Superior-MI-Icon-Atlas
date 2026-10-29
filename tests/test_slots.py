"""Prevent malformed compatibility contracts from entering a Bag or exported package."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from tools.validate_visual_pack import check
from tools.build_site import ROOT


class SlotPackContracts(unittest.TestCase):
    def setUp(self):
        self.data={}
        with zipfile.ZipFile(ROOT/'web/demo/potions-collection.zip') as z:
            for path in z.namelist(): self.data[path]=z.read(path)

    def check_mutation(self, relative, edit):
        obj=json.loads(self.data[relative]);edit(obj)
        self.data[relative]=json.dumps(obj).encode()
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'test.zip'
            with zipfile.ZipFile(file,'w',zipfile.ZIP_DEFLATED) as z:
                for name,data in self.data.items():z.writestr(name,data)
            return check(file)

    def test_reference_fixture(self):
        self.assertEqual(check(ROOT/'web/demo/potions-collection.zip'),[])

    def test_invalid_default_option(self):
        err=self.check_mutation('packs/bottle/manifest.json',lambda p:p['assets'][2]['slots']['fluid'].update({'default':'smi.fake'}))
        self.assertTrue(any('default not in options' in e for e in err),err)

    def test_unapproved_slot_asset(self):
        err=self.check_mutation('packs/bottle/manifest.json',lambda p:p['assets'][2]['slots']['fluid']['options'].append('smi.potion.base'))
        self.assertTrue(any('lacks interface' in e for e in err),err)

    def test_contract_wrong_size(self):
        err=self.check_mutation('packs/fluids/manifest.json',lambda p:p['assets'][0].update({'logical_size_px':[60,60]}))
        self.assertTrue(any('incompatible dimensions' in e for e in err),err)

    def test_bad_preset(self):
        err=self.check_mutation('packs/bottle/manifest.json',lambda p:p['assets'][2]['presets']['Mana']['slots'].update({'fluid':'smi.unknown'}))
        self.assertTrue(any('bad preset slot' in e for e in err),err)

    def test_invalid_schema_must_not_crash_validator(self):
        err=self.check_mutation('packs/bottle/manifest.json',lambda p:p['assets'][2]['slots']['fluid'].pop('accepts'))
        self.assertTrue(err)
        self.assertTrue(any('required property' in e for e in err),err)

if __name__=='__main__': unittest.main()
