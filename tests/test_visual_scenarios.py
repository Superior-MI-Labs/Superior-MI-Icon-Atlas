"""The reusable Chromium scenario format must reject malformed acceptance recipes."""
import importlib.util
import json
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory
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
        self.assertEqual(len(self.data['cases']), 22)
        names={case['pack'] for case in self.data['cases']}
        self.assertEqual(names, {'interactive-hud.zip','character-animations.zip','animated-icons.zip','starter-pack.zip','potions-collection.zip','royal-forge-hud-resources.zip','royal-forge-controls.zip','royal-forge-complete.zip','minimal-white-tech.zip'})
        for name in names:
            self.assertTrue((ROOT/'web/demo'/name).is_file() or (ROOT/'examples'/name.removesuffix('.zip')/'manifest.json').is_file(),name)

    def test_collection_visual_specs(self):
        ids = {case['id'] for case in self.data['cases']}
        for path in sorted((ROOT/'tests/visual-packs').glob('*/*.json')):
            recipe = json.loads(path.read_text())
            module.verify_spec(recipe)
            for case in recipe['cases']:
                self.assertEqual(case['pack'], path.parent.name + '.zip')
                self.assertNotIn(case['id'], ids)
                ids.add(case['id'])

    def test_external_archive_uses_authored_builder(self):
        self.assertEqual(module.builder_root_for(None),module.SITE)
        self.assertEqual(module.builder_root_for(Path('candidate.zip')),ROOT/'web')
        self.assertIn('id="stage"',module.loaded_html(ROOT/'web'))
        for path in module.SCRIPTS:
            self.assertTrue((ROOT/'web'/path).is_file(),path)

    def test_scoped_runner_selects_only_requested_suites_and_fails_closed(self):
        import os
        import shutil
        import subprocess
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            shutil.copyfile(ROOT/'RUN-ALL.sh',root/'RUN-ALL.sh')
            for slug in ('first','second'):
                (root/'examples'/slug).mkdir(parents=True)
                folder=root/'tests/visual-packs'/slug
                folder.mkdir(parents=True)
                (folder/'one.json').touch()
            (root/'tests/visual-packs/first/two.json').touch()
            (root/'bin').mkdir()
            stub=root/'bin/python3'
            stub.write_text('#!/bin/sh\n[ "$1" = -c ] && exit 0\n'
                            'printf "%s\\n" "$*" >> "$TRACE"\n'
                            'case "$*" in *"$FAIL_MATCH"*) [ -z "$FAIL_MATCH" ] || exit 7;; esac\n')
            stub.chmod(0o755)
            trace=root/'trace'
            def invoke(*args,fail=''):
                trace.write_text('')
                env=dict(os.environ,PATH=str(root/'bin')+os.pathsep+os.environ['PATH'],
                         TRACE=str(trace),FAIL_MATCH=fail)
                result=subprocess.run(['bash',str(root/'RUN-ALL.sh'),*args],
                    cwd=root,env=env,capture_output=True,text=True)
                return result,trace.read_text().splitlines()
            result,calls=invoke('--collection','first',str(root/'scoped'))
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(len(calls),4,calls)
            self.assertIn('tools/build_site.py --collection first',calls[0])
            self.assertIn('tools/qualify_asset_zip.py',calls[1])
            self.assertTrue(all('--archive' in c and 'visual-packs/first/' in c for c in calls[2:]))
            self.assertNotIn('second','\n'.join(calls))
            result,calls=invoke('--collection-regressions',str(root/'regression'))
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(len(calls),3,calls)
            self.assertTrue(all('browser_visual_matrix.py' in c and '--archive' not in c for c in calls))
            result,calls=invoke('--collection','first',str(root/'failed'),fail='qualify_asset_zip.py')
            self.assertEqual(result.returncode,7)
            self.assertEqual(len(calls),2)
            self.assertNotIn('COLLECTION SCENARIOS PASS',result.stdout)
            for args in (('--collection','../escape'),('--collection','missing'),('--collection',)):
                result,calls=invoke(*args)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(calls,[])
            for spec in (root/'tests/visual-packs').glob('*/*.json'):
                spec.unlink()
            result,calls=invoke('--collection-regressions',str(root/'empty'))
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(calls,[])

    def test_exact_archive_override(self):
        with TemporaryDirectory() as tmp:
            archive=Path(tmp)/'candidate.zip';archive.touch()
            single={'cases':[self.data['cases'][0]]}
            module.verify_archive_override(single,archive)
            self.assertEqual(module.archive_for_case(single['cases'][0],archive),archive)
            self.assertEqual(module.archive_for_case(single['cases'][0]),module.SITE/'demo'/single['cases'][0]['pack'])
            with self.assertRaisesRegex(ValueError,'single pack'):
                module.verify_archive_override(self.data,archive)
            with self.assertRaisesRegex(ValueError,'not found'):
                module.verify_archive_override(single,archive.with_name('absent.zip'))

    def test_duplicate_case_ids_fail(self):
        self.data['cases'].append(self.data['cases'][0])
        with self.assertRaisesRegex(ValueError,'Duplicate case ID'):
            module.verify_spec(self.data)

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

    def test_changed_area_requires_proportional_monotonic_visible_fill(self):
        def filled(n):
            im=Image.new('RGBA',(100,10),(20,20,20,255))
            if n:im.paste((200,220,255,255),(0,0,n,10))
            return im
        points=[{'sample':str(n),'fraction':n/100} for n in (0,1,5,25,50,99,100)]
        case={'assertions':[{'type':'changed_area_fraction','samples':points}]}
        images={p['sample']:filled(int(p['sample'])) for p in points}
        self.assertEqual(module.check_case(case,images,{})[0]['status'],'PASS')
        for label,n in [('1',0),('50',75),('99',100)]:
            bad={**images,label:filled(n)}
            self.assertEqual(module.check_case(case,bad,{})[0]['status'],'FAIL')

    def test_changed_area_rejects_invalid_fraction_spec(self):
        case=self.data['cases'][0]
        labels=[x['id'] for x in case['samples']]
        case['assertions']=[{'type':'changed_area_fraction','samples':[
            {'sample':labels[0],'fraction':0},{'sample':labels[1],'fraction':0.75},
            {'sample':labels[2],'fraction':0.5}]}]
        with self.assertRaisesRegex(ValueError,'increasing fractions'):
            module.verify_spec(self.data)

    def test_deliberately_wrong_visual_expectation_fails(self):
        a=Image.new('RGBA',(24,24),(0,0,0,0))
        b=a.copy();b.paste((20,220,50,255),(0,0,10,10))
        case={'assertions':[{'type':'same','a':'one','b':'two','max_changed_pixels':0},
                            {'type':'different','a':'one','b':'two','min_changed_pixels':20}]}
        findings=module.check_case(case,{'one':a,'two':b},{'one':'','two':''})
        self.assertEqual([x['status'] for x in findings],['FAIL','PASS'])

if __name__=='__main__':unittest.main()
