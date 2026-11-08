"""Public catalog is built only from explicitly approved source collections."""
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from tools.build_site import build,ROOT
from tools.prune_public_site import prune
from tools.validate_visual_pack import check

class PublicCatalogTests(unittest.TestCase):
    def test_public_approval_and_manifest_derived_records(self):
        with tempfile.TemporaryDirectory() as temp:
            site=Path(temp);build(site)
            public=json.loads((site/'public-catalog.json').read_text())
            self.assertEqual(public['schema'],'smi-public-catalog/1')
            self.assertEqual(len(public['packs']),1+len(json.loads((ROOT/'publications.json').read_text())['collections']))
            self.assertEqual(public['legacy_count'],2073)
            publication=json.loads((ROOT/'publications.json').read_text())
            expected_count=sum(c['expected_assets'] for c in publication['collections'])
            self.assertGreaterEqual(expected_count,709)
            self.assertEqual(public['approved_count'],expected_count)
            self.assertTrue(all(c['visual_qa'] in ('pending','reviewed') for c in publication['collections']))
            self.assertEqual({a['visual_qa'] for a in public['assets'] if not a.get('legacy')},{'reviewed','pending'})
            self.assertIn('pixel-fantasy-icons',{p['id'] for p in public['packs']})
            self.assertEqual(public['packs'][0]['id'],'fantasy-rpg-hud-wave1')
            approved=set()
            for entry in publication['collections']:
                folder=ROOT/entry['path']
                source=json.loads((folder/'manifest.json').read_text())
                self.assertEqual(len(source['assets']),entry['expected_assets'])
                approved.update(a['id'] for a in source['assets'])
                archive=site/'demo'/(folder.name+'.zip')
                self.assertEqual(check(archive),[],str(archive))
                self.assertTrue(archive.is_file())
                if folder.name=='pixel-fantasy-icons':
                    with ZipFile(archive) as z:
                        self.assertFalse(any(n.startswith('source-') or n.startswith('qa/') or n=='authoring.json' for n in z.namelist()))
            self.assertEqual(approved,{a['id'] for a in public['assets'] if not a.get('legacy')})
            self.assertEqual(len(public['assets']),2073+expected_count)
            self.assertEqual(public['synonyms'],json.loads((ROOT/'manifest.json').read_text())['search']['synonyms'])
            self.assertIn('white-geometric-monoline',public['styles'])
            archive=[a for a in public['assets'] if a.get('legacy')]
            self.assertTrue(all(a.get('domain') and a.get('review_status') for a in archive))
            self.assertTrue(any(a.get('concept_id') for a in archive))
            self.assertEqual(len({a['id'] for a in public['assets']}),2073+expected_count)
            self.assertTrue(all(a.get('style') for a in public['assets']))
            for field in ('domain','style','subject','review','status','license','animated'):
                self.assertIn('id="'+field+'"',(site/'index.html').read_text())
            self.assertEqual(check(site/'demo/fantasy-rpg-hud-wave1.zip'),[])
            self.assertTrue(all(a['license']=='CC0-1.0' for a in public['assets'] if not a.get('legacy')))
            self.assertEqual(sum(a.get('legacy',False) for a in public['assets']),2073)
            home=(site/'index.html').read_text().lower()
            self.assertNotIn('browse the 2,073-icon library',home)
            self.assertNotIn('white geometric monoline',home)
            self.assertNotIn('explore asset packs and starter templates',home)
            self.assertNotIn('featured.js',home)
            self.assertIn('asset-renderer.js',home)
            self.assertNotIn('catalog-data.js',home)
            self.assertIn('public-catalog.json',(site/'app.js').read_text())
            self.assertIn('asset-renderer.js',(site/'builder.html').read_text())
    def test_transparent_storyforge_atlas_cells_do_not_cut_through_neighbor_art(self):
        """Every crop boundary must lie in a transparent gutter, not across an icon."""
        from PIL import Image
        atlas_dirs=sorted((ROOT/'examples').glob('storyforge-atlases-*'))
        sheet_count=0
        region_count=0
        for folder in atlas_dirs:
            manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
            for texture_id,texture in manifest['textures'].items():
                with Image.open(folder/texture['path']) as image:
                    foreground=image.getchannel('A').point(lambda alpha:255 if alpha>16 else 0)
                    regions=[a for a in manifest['assets'] if a.get('texture')==texture_id
                             and a.get('rect_px')!=[0,0,image.width,image.height]]
                    rows={}
                    for asset in regions:
                        x,y,w,h=asset['rect_px']
                        self.assertGreater(min(w,h),0,asset['id'])
                        self.assertLessEqual(x+w,image.width,asset['id'])
                        self.assertLessEqual(y+h,image.height,asset['id'])
                        self.assertIsNotNone(foreground.crop((x,y,x+w,y+h)).getbbox(),asset['id'])
                        rows.setdefault(y,[]).append(asset)
                        region_count+=1
                    y_end=0
                    for y,row in sorted(rows.items()):
                        self.assertEqual(y,y_end,(texture_id,'row start'))
                        row.sort(key=lambda a:a['rect_px'][0])
                        x_end=0
                        for asset in row:
                            x,_,w,h=asset['rect_px']
                            self.assertEqual(x,x_end,(asset['id'],'column start'))
                            if x:
                                self.assertIsNone(foreground.crop((x,y,x+1,y+h)).getbbox(),
                                                  (asset['id'],'neighboring icon on left edge'))
                            x_end=x+w
                        self.assertEqual(x_end,image.width,(texture_id,'last column'))
                        if y:
                            self.assertIsNone(foreground.crop((0,y,image.width,y+1)).getbbox(),
                                              (texture_id,'neighboring icon on top edge'))
                        y_end=y+row[0]['rect_px'][3]
                    self.assertEqual(y_end,image.height,(texture_id,'last row'))
                    sheet_count+=1
        self.assertGreaterEqual(sheet_count,24)
        self.assertGreaterEqual(region_count,1536)

    def test_deployed_site_excludes_old_public_files_and_starter_zips(self):
        with tempfile.TemporaryDirectory() as temp:
            site=Path(temp);build(site)
            self.assertEqual(prune(site),len(json.loads((ROOT/'publications.json').read_text())['collections']))
            self.assertTrue((site/'demo/fantasy-rpg-hud-wave1.zip').is_file())
            self.assertTrue((site/'demo/royal-forge-controls.zip').is_file())
            self.assertTrue((site/'demo/royal-forge-hud-resources.zip').is_file())
            self.assertTrue((site/'demo/pixel-fantasy-icons.zip').is_file())
            self.assertIn('fantasy-rpg-hud-wave1.zip',(site/'ai-guide.html').read_text())
            for doc in (site/'ai').rglob('*.md'):
                self.assertNotRegex(doc.read_text(),r'\]\((?:\.\./)+demo/(?:icons|animated-icons|character-animations|interactive-hud|starter-pack|potions-collection)\.zip\)')
            for rel in ('catalog-data.js','featured-packs.json','manifest.json','manifests','demo/starter-pack.zip','demo/animated-icons.zip','demo/interactive-hud.zip'):
                self.assertFalse((site/rel).exists(),rel)
            self.assertEqual(len(list(site.glob('sheets/*/atlas.png'))),20)
            self.assertFalse(list(site.glob('sheets/*/black-outline.png')))

    def test_legacy_sources_remain_archived(self):
        self.assertTrue((ROOT/'manifest.json').is_file())
        self.assertTrue((ROOT/'examples/icons/manifest.json').is_file())
        public=json.loads((ROOT/'publications.json').read_text())
        self.assertEqual(public['collections'][0]['path'],'examples/fantasy-rpg-hud-wave1')

if __name__=='__main__':unittest.main()