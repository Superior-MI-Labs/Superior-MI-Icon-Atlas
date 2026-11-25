"""Published asset coverage and review provenance guards."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.asset_inventory import audit, source_collections, read_collection, runtime_files
from tools.build_site import ROOT

class InventoryTests(unittest.TestCase):
    def test_source_to_public_registry_reconciliation(self):
        r=audit(ROOT);self.assertEqual(r["errors"],[],r["errors"])
        sources={p.relative_to(ROOT).as_posix() for p in source_collections(ROOT)}
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
    def test_multi_manifest_source_and_payload_agree(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);folder=root/"examples"/"multi"
            for name in ("first","second"):
                pack_dir=folder/"packs"/name
                (pack_dir/"textures").mkdir(parents=True)
                (pack_dir/"textures"/"sheet.png").write_bytes(b"fixture")
                (pack_dir/"LICENSE.txt").write_text("fixture notice")
                (pack_dir/"manifest.json").write_text(json.dumps({
                    "schema":"smi-visual-pack/1","pack_id":name,
                    "assets":[{"id":name,"name":name,"tags":["fixture"]}],
                    "textures":{"sheet":{"path":"textures/sheet.png"}}}))
            index={"schema":"smi-visual-collection/1","packs":[
                {"manifest":"packs/first/manifest.json"},{"manifest":"packs/second/manifest.json"}]}
            (folder/"collection.json").write_text(json.dumps(index))
            policy={"schema":"smi-publications/1","collections":[{"path":"examples/multi",
                "expected_assets":2,"approval":"owner","rights":"owned","visual_qa":"pending"}]}
            (root/"publications.json").write_text(json.dumps(policy))
            report=audit(root)
            self.assertEqual(report["errors"],[])
            self.assertEqual(report["summary"]["published_assets"],2)
            loaded,packs=read_collection(folder);files,textures=runtime_files(folder,loaded,packs)
            self.assertEqual(len(textures),2)
            self.assertEqual({p.relative_to(folder).as_posix() for p in files},
                {"collection.json",*(f"packs/{name}/{file}" for name in ("first","second")
                 for file in ("manifest.json","textures/sheet.png","LICENSE.txt"))})
            index["packs"][1]["manifest"]="../escape.json"
            (folder/"collection.json").write_text(json.dumps(index))
            self.assertTrue(any("unsafe source path" in error for error in audit(root)["errors"]))

    def test_bundle_rejects_unpublished_and_recursive_dependencies(self):
        from tools.asset_inventory import archive_payload
        folder=ROOT/'examples'/'royal-forge-complete'
        index,packs=read_collection(folder)
        records=json.loads((ROOT/'publications.json').read_text())['collections']
        record=next(r for r in records if r['path']=='examples/royal-forge-complete')
        files,generated=archive_payload(ROOT,folder,index,packs,record,records)
        self.assertEqual(len(generated['packs']),3)
        self.assertIn('packs/royal-forge-controls/manifest.json',files)
        for includes in (['examples/missing'],[record['path']],['../unsafe'],[record['includes'][0]]*2):
            with self.subTest(includes=includes),self.assertRaises(ValueError):
                archive_payload(ROOT,folder,index,packs,dict(record,includes=includes),records)

    def test_orphan_and_id_collision_visible(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ("a","b"):
                folder=root/"examples"/name;folder.mkdir(parents=True)
                (folder/"manifest.json").write_text(json.dumps({"schema":"smi-visual-pack/1","assets":[{"id":"shared"}],"textures":{}}))
            (root/"publications.json").write_text(json.dumps({"schema":"smi-publications/1","collections":[]}))
            self.assertTrue(any("Duplicate asset ID" in e for e in audit(root)["errors"]))

if __name__=="__main__":unittest.main()
