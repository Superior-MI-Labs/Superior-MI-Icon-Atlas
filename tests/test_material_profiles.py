"""Material source integrity and existing schema/archive pipeline regression."""
import hashlib, json, tempfile, unittest
from pathlib import Path
from PIL import Image
from jsonschema import Draft202012Validator
from tools.build_site import ROOT, build_one_collection
from tools.validate_visual_pack import check, validate_material_profiles

class MaterialProfileTests(unittest.TestCase):
    def test_gflow_source_integrity(self):
        schema=Draft202012Validator(json.loads((ROOT/'schemas/smi-visual-pack-v1.schema.json').read_text()))
        collection=Draft202012Validator(json.loads((ROOT/'schemas/smi-visual-collection-v1.schema.json').read_text()))
        ids=set(); hashes=set(); count=0
        folders=sorted((ROOT/'examples').glob('gflow-materials-*'))
        self.assertEqual(len(folders),15)
        for folder in folders:
            p=json.loads((folder/'manifest.json').read_text()); c=json.loads((folder/'collection.json').read_text())
            schema.validate(p);collection.validate(c)
            self.assertEqual(p['license'],'CC0-1.0');self.assertIn(c['entry_asset'],{a['id'] for a in p['assets']})
            self.assertEqual(len(p['assets']),len(p['textures']))
            for a in p['assets']:
                t=p['textures'][a['texture']]; self.assertEqual(validate_material_profiles(a,t),[])
                f=folder/t['path'];self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),t['sha256'])
                with Image.open(f) as im:im.load();self.assertEqual(im.size,(1024,1024));self.assertEqual(im.mode,'RGB')
                self.assertNotIn(a['id'],ids);ids.add(a['id']);h=a['material']['source']['sha256'];self.assertNotIn(h,hashes);hashes.add(h);count+=1
        self.assertEqual(count,302)
        records=json.loads((ROOT/'publications.json').read_text())['collections']; self.assertEqual(sum(r['expected_assets'] for r in records if r['path'].startswith('examples/gflow-materials-')),302)
    def test_existing_archive_validator(self):
        with tempfile.TemporaryDirectory() as td:
            for folder in sorted((ROOT/'examples').glob('gflow-materials-*')):
                f=Path(td)/(folder.name+'.zip'); build_one_collection(folder.name,f)
                self.assertLess(f.stat().st_size,95*1024*1024);self.assertEqual(check(f),[],folder.name);f.unlink()
    def test_catalog_projection_if_built(self):
        path=ROOT/'site/public-catalog.json'
        if not path.exists():self.skipTest('Build site first to qualify catalog projection')
        c=json.loads(path.read_text()); selected=[a for a in c['assets'] if a['id'].startswith('smi.material.gflow.')]
        self.assertEqual(len(selected),302)
        packs={p['id']:p for p in c['packs']}
        for a in selected:
            self.assertEqual(a['material']['channels']['base_color'],'self');self.assertEqual(sum(x['weight_bp'] for x in a['visual_profile']['palette']),10000)
            self.assertIn('surface-material',a['capabilities']);self.assertIn('textures',a['category_path']);self.assertTrue(a.get('thumbnail'));self.assertEqual(a['visual_qa'],'pending')
            self.assertTrue(packs[a['pack']].get('archive_sha256'))
