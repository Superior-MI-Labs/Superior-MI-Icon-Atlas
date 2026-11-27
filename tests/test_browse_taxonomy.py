import unittest
from tools.browse_taxonomy import classify, load_taxonomy, project_browse

class BrowseTaxonomyTests(unittest.TestCase):
    def setUp(self):self.taxonomy=load_taxonomy()
    def test_parent_paths_and_precedence(self):
        asset={'pack':'fantasy-recovered-chests-20261125','domain':'world-environment'}
        result=classify(asset,{},self.taxonomy)
        self.assertEqual(result['category_path'],['world','world.props','world.props.containers','world.props.containers.chests'])
        self.assertEqual(result['perspective'],['isometric','billboard'])
        result=classify({**asset,'classification':{'perspective':['top-down']}},{'perspective':['front-view']},self.taxonomy)
        self.assertEqual(result['perspective'],['top-down'])
    def test_unknown_and_invalid(self):
        asset={'pack':'new-pack'}
        self.assertEqual(classify(asset,{},self.taxonomy)['perspective'],['unknown'])
        with self.assertRaises(ValueError):classify(asset,{'category_path':['invented']},self.taxonomy)
        with self.assertRaises(ValueError):classify(asset,{'perspective':['isometric','isometric']},self.taxonomy)
    def test_counts_dont_duplicate_assets(self):
        assets=[{'pack':'x','id':'a','classification':{'category_path':['world.props.containers.chests','items']}},{'pack':'x','id':'b','discovery':'component'}]
        packs=[{'id':'x'}]
        project_browse(assets,packs,{},self.taxonomy)
        self.assertEqual(packs[0]['asset_count'],2)
        self.assertEqual(packs[0]['listed_count'],1)
        self.assertIn('world',packs[0]['categories'])
        self.assertEqual(len(assets),2)
