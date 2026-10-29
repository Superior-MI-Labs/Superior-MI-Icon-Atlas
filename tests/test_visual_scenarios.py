"""The reusable Chromium scenario format must reject malformed acceptance recipes."""
import importlib.util
import json
from pathlib import Path
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('visual_matrix', ROOT/'tests/browser_visual_matrix.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class VisualScenarioContractTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/'tests/visual-scenarios.json').read_text())

    def test_scenario_schema_and_coverage(self):
        module.verify_spec(self.data)
        self.assertEqual(len(self.data['cases']), 5)
        names={case['pack'] for case in self.data['cases']}
        self.assertEqual(names, {'interactive-hud.zip','character-animations.zip','animated-icons.zip','starter-pack.zip','potions-collection.zip'})
        for name in names:
            self.assertTrue((ROOT/'web/demo'/name).is_file() or (ROOT/'examples'/name.removesuffix('.zip')/'manifest.json').is_file(),name)

    def test_unknown_assertion_fails(self):
        self.data['cases'][0]['assertions'][0]['type']='magic_visual_quality'
        with self.assertRaisesRegex(ValueError, 'unsupported assertion'):
            module.verify_spec(self.data)

    def test_assertion_must_reference_real_sample(self):
        self.data['cases'][0]['assertions'][1]['sample']='absent'
        with self.assertRaisesRegex(ValueError, 'missing sample'):
            module.verify_spec(self.data)

    def test_pixel_diff_distinguishes_images(self):
        empty=Image.new('RGBA',(12,12),(0,0,0,0))
        altered=empty.copy()
        altered.putpixel((1,2),(15,140,30,255))
        self.assertEqual(module.pixel_change(empty,empty),0)
        self.assertEqual(module.pixel_change(empty,altered),1)
        self.assertEqual(module.green_count(empty),0)
        self.assertEqual(module.green_count(altered),1)

    def test_deliberately_wrong_visual_expectation_fails(self):
        a=Image.new('RGBA',(24,24),(0,0,0,0))
        b=a.copy();b.paste((20,220,50,255),(0,0,10,10))
        case={'assertions':[{'type':'same','a':'one','b':'two','max_changed_pixels':0},
                            {'type':'different','a':'one','b':'two','min_changed_pixels':20}]}
        findings=module.check_case(case,{'one':a,'two':b},{'one':'','two':''})
        self.assertEqual([x['status'] for x in findings],['FAIL','PASS'])

if __name__=='__main__':unittest.main()
