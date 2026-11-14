"""Experimental motion video showcase uses one source manifest and valid media.

The Visual Atlas canonical asset types remain unchanged: this tests a web preview,
not artwork approval or a new runtime rendering contract.
"""
import hashlib
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT/'web'


class MotionLabTests(unittest.TestCase):
    def test_footage_registry_and_sources(self):
        doc=json.loads((WEB/'sky-motion-lab'/'clips.json').read_text())
        self.assertEqual(doc['schema'],'smi-video-showcase/1')
        self.assertEqual(len(doc['clips']),5)
        ids=set()
        for clip in doc['clips']:
            slug=clip['id']
            self.assertRegex(slug,r'^[a-z0-9_]+$')
            self.assertNotIn(slug,ids);ids.add(slug)
            self.assertIn(clip['kind'],('idle','run','sprint'))
            self.assertGreaterEqual(clip['frames'],2)
            self.assertGreaterEqual(clip['duration_ms'],100)
            self.assertEqual(clip['fps'],16)
            for ext in ('webm','mp4','jpg'):
                relative=clip['poster' if ext=='jpg' else ext]
                self.assertTrue(relative.startswith('sky-motion-lab/media/'))
                self.assertRegex(relative,r'^sky-motion-lab/media/[a-z0-9_]+\.'+ext+'$')
                path=WEB/relative
                self.assertTrue(path.is_file(),relative)
                self.assertGreater(path.stat().st_size,500)
                self.assertLess(path.stat().st_size,8*1024*1024)
                if ext=='webm':
                    self.assertEqual(path.read_bytes()[:4],b'\x1aE\xdf\xa3')
            if shutil.which('ffprobe'):
                probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                    '-of','default=nw=1:nk=1',str(WEB/clip['mp4'])],capture_output=True,text=True,check=True)
                self.assertGreater(float(probe.stdout),2)
        self.assertEqual(ids,{'idle','run','sprint_a','sprint_b','sprint_c'})

    def test_page_keeps_existing_asset_contract_separate(self):
        page=(WEB/'sky-motion-lab.html').read_text()
        script=(WEB/'sky-motion-lab/app.js').read_text()
        self.assertIn('sky-motion-lab/clips.json',script)
        self.assertIn('Play sequence',page)
        self.assertIn('Loop single clip',page)
        self.assertIn('Repeat entire sequence',page)
        self.assertIn('Original MP4',page)
        self.assertIn('Transparent WebM',page)
        self.assertIn('sky-motion-lab.html',(WEB/'index.html').read_text())
        self.assertIn('sky-motion-lab.html',(ROOT/'tools'/'build_site.py').read_text())
        self.assertNotIn('new state_set',script)

if __name__=='__main__':unittest.main()
