"""Validate canonical stat profiles and reject broken cross-references."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from tools.validate_visual_pack import check

ROOT=Path(__file__).resolve().parents[1]

class StatProfileValidationTests(unittest.TestCase):
    def fixture(self,kind):
        folder=ROOT/"examples"/kind
        data=json.loads((folder/"manifest.json").read_text())
        return folder,data

    def qualify(self,folder,pack):
        with tempfile.TemporaryDirectory() as temp:
            archive=Path(temp)/"stat-test.zip"
            with ZipFile(archive,'w',ZIP_DEFLATED) as z:
                z.writestr("manifest.json",json.dumps(pack))
                for t in pack["textures"].values():
                    z.write(folder/t["path"],t["path"])
            return check(archive)

    def test_both_authored_examples(self):
        for kind in ("interactive-hud","character-animations"):
            with self.subTest(kind=kind):
                folder,pack=self.fixture(kind)
                self.assertEqual(self.qualify(folder,pack),[])

    def test_invalid_cost_stat_range_event_binding_and_duplicate(self):
        folder,base=self.fixture("character-animations")
        mutations=[
            lambda p:p["stat_profiles"][0]["actions"]["dash"]["costs"].update({"ghost":9}),
            lambda p:p["stat_profiles"][0]["stats"]["stamina"].update({"initial":101}),
            lambda p:p["stat_profiles"][0]["actions"]["dash"].update({"emit":"missing_event"}),
            lambda p:p["stat_profiles"][0]["bindings"][0].update({"input":"animation"}),
            lambda p:p["stat_profiles"].append(copy.deepcopy(p["stat_profiles"][0])),
        ]
        for mutate in mutations:
            pack=copy.deepcopy(base);mutate(pack)
            with self.subTest(mutation=mutate):
                self.assertTrue(self.qualify(folder,pack))

    def test_incompatible_input_range(self):
        folder,pack=self.fixture("interactive-hud")
        pack["stat_profiles"][0]["stats"]["energy"]["max"]=200
        self.assertTrue(any("stat binding" in e or "invalid" in e for e in self.qualify(folder,pack)))

if __name__=="__main__":unittest.main()
