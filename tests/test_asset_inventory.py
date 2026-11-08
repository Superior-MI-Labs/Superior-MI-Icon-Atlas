"""Published asset coverage and review provenance guards."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.asset_inventory import audit
from tools.build_site import ROOT

class InventoryTests(unittest.TestCase):
    def test_source_to_public_registry_reconciliation(self):
        r=audit(ROOT);self.assertEqual(r["errors"],[],r["errors"])
        sources={p.parent.relative_to(ROOT).as_posix() for p in (ROOT/"examples").glob("*/manifest.json")}
        self.assertEqual(sources,{c["path"] for c in r["collections"]})
        policy=json.loads((ROOT/"publications.json").read_text())
        self.assertEqual({p["path"] for p in policy["collections"]},
            {c["path"] for c in r["collections"] if c["published"]})
        self.assertEqual(r["summary"]["published_assets"],sum(p["expected_assets"] for p in policy["collections"]))
        self.assertEqual(r["summary"]["published_pending_visual_review"],
            sum(p["visual_qa"]=="pending" for p in policy["collections"]))
    def test_missing_review_and_unpublished_assets(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);folder=root/"examples"/"sample";folder.mkdir(parents=True)
            (folder/"manifest.json").write_text(json.dumps({"schema":"smi-visual-pack/1","assets":[{"id":"a","name":"A","tags":["test"]}],"textures":{}}))
            policy={"schema":"smi-publications/1","collections":[{"path":"examples/sample","expected_assets":1,"approval":"owner","rights":"owned"}]}
            (root/"publications.json").write_text(json.dumps(policy))
            self.assertTrue(any("visual review" in e for e in audit(root)["errors"]))
            policy["collections"][0]["visual_qa"]="pending"
            (root/"publications.json").write_text(json.dumps(policy))
            self.assertEqual(audit(root)["errors"],[])
            policy["collections"].clear();(root/"publications.json").write_text(json.dumps(policy))
            self.assertEqual(audit(root)["summary"]["unpublished_collections"],1)
    def test_orphan_and_id_collision_visible(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ("a","b"):
                folder=root/"examples"/name;folder.mkdir(parents=True)
                (folder/"manifest.json").write_text(json.dumps({"schema":"smi-visual-pack/1","assets":[{"id":"shared"}],"textures":{}}))
            (root/"publications.json").write_text(json.dumps({"schema":"smi-publications/1","collections":[]}))
            self.assertTrue(any("Duplicate asset ID" in e for e in audit(root)["errors"]))

if __name__=="__main__":unittest.main()
