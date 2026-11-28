import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from tools.build_site import build_one_collection, ROOT
from tests.site_fixture import shared_site, fixture
from atlasctl import validate,load,search_icons

class AtlasContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=load()

    def test_source_of_truth(self):
        self.assertEqual(self.m['schema'],'smi-icon-atlas/3')
        self.assertEqual(len(self.m['icons']),2073)
        self.assertEqual(len(self.m['sheets']),20)
        self.assertEqual(len({i['id'] for i in self.m['icons']}),2073)
        self.assertTrue(all(i['provenance']['source_path'].startswith('source-images/') for i in self.m['icons']))
        self.assertLess((ROOT/'manifest.json').stat().st_size,30000)
        self.assertTrue((ROOT/'manifests/programming-00.json').is_file())

    def test_images_and_metadata(self):
        self.assertEqual(validate(deep=True),[])
        for s in self.m['sheets']:
            # Duplicate legacy mask files were removed; white atlas supplies the tint alpha.
            self.assertEqual(s['foreground_mask'],s['path'])
            self.assertFalse((ROOT/Path(s['path']).parent/'foreground-mask.png').exists())
            self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
        flame=next(i for i in self.m['icons'] if i['id']=='icons.candidate.programming.r04i19')
        self.assertEqual(flame['rect_px'],{'x':1824,'y':384,'w':96,'h':96})
        self.assertEqual(flame['name'],'Flame')

    def test_relevant_searches(self):
        for term,target in [('fire','programming.r04i19'),('flame','programming.r04i19'),('burn','programming.r04i19'),('picture','files-media.r02i12'),('photo','files-media.r02i12'),('image','files-media.r02i12'),('lambda','programming.r00i02'),('terminal','programming.r00i04'),('folder','programming.r00i06')]:
            hits=search_icons(term,manifest=self.m)
            self.assertTrue(hits,term)
            self.assertTrue(any(target in icon['id'] for icon in hits),term)
        self.assertEqual(search_icons('fire',manifest=self.m,status='unreviewed'),[])
        self.assertEqual(search_icons('flame',manifest=self.m,domain='hardware'),[])
        self.assertTrue(search_icons('fire',manifest=self.m,style='white-geometric-monoline'))

    def test_reviewed_visual_metadata(self):
        reviewed=[i for i in self.m['icons'] if i['review_status']=='reviewed']
        self.assertEqual(len(reviewed),734)
        for i in reviewed:
            self.assertTrue(i['name'] and not i['name'].startswith('Unreviewed glyph'),i['id'])
            self.assertTrue(i['tags'] and i['subjects'],i['id'])
            if i['id'].startswith('icons.candidate') and i['domain'] in {'developer-tools','network-cloud','ui-controls','data-ai'}:
                self.assertTrue(i['concept_id'],i['id'])
            self.assertEqual(len(i['tags']),len(set(t.casefold() for t in i['tags'])),i['id'])
        self.assertEqual(len([i for i in self.m['icons'] if i['review_status']=='unreviewed']),1339)
        self.assertTrue(any(i['name']=='Microchip' for i in search_icons('microchip',manifest=self.m)[:8]))
        self.assertTrue(any(i['name']=='Wireless router' for i in search_icons('router',manifest=self.m)[:10]))
        self.assertTrue(any(i['name']=='Image stack' or i['name']=='Picture' for i in search_icons('photo',manifest=self.m)[:20]))
        self.assertEqual(search_icons('flame',manifest=self.m,domain='hardware'),[])
        self.assertTrue(search_icons('keyboard',manifest=self.m,domain='hardware'))

    def test_site_generation(self):
        with tempfile.TemporaryDirectory() as temp, shared_site() as dest:
            self.assertEqual(fixture.build_count,2073)
            self.assertTrue((dest/'index.html').is_file())
            self.assertTrue((dest/'catalog-data.js').is_file())
            self.assertTrue((dest/'manifests/programming-00.json').is_file())
            self.assertTrue((dest/'sheets/developer-tools-00/atlas.png').is_file())
            self.assertFalse((dest/'sheets/developer-tools-00/foreground-mask.png').exists())
            text=(dest/'catalog-data.js').read_text()
            self.assertIn('nature.flame',text)
            self.assertIn('white-geometric-monoline',text)
            self.assertIn('picture',text)
            # Single-collection mode must create the exact same bytes as Pages,
            # including bundled dependencies, without invoking the full build.
            for slug in ('painterly-fantasy-woodland','royal-forge-complete'):
                target=Path(temp)/(slug+'.zip')
                build_one_collection(slug,target)
                self.assertEqual(target.read_bytes(),(dest/'demo'/target.name).read_bytes())

    def test_scoped_collection_rejects_unsafe_or_unknown_slug(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'candidate.zip'
            for slug in ('../examples','/tmp','unknown-collection-987654'):
                with self.subTest(slug=slug),self.assertRaises(ValueError):
                    build_one_collection(slug,target)
                self.assertFalse(target.exists())

if __name__=='__main__':unittest.main()
